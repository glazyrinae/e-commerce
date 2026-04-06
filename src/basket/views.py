import json
import logging
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import IntegerField, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce
from django.http import HttpRequest, JsonResponse
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from basket.models import Basket
from products.models import Colors, Products, Sizes, Store

logger = logging.getLogger(__name__)

def _get_effective_price(product: Products) -> Decimal:
    if product.discount_price is not None:
        return product.discount_price
    if product.price is not None:
        return product.price
    return Decimal("0")


def _get_cart_totals(user) -> tuple[int, Decimal]:
    cart_items = Basket.objects.filter(user=user).select_related("product")
    total_items = sum(item.quantity for item in cart_items)
    total_price = sum(
        _get_effective_price(item.product) * item.quantity for item in cart_items
    )
    return total_items, total_price


def _get_stock_count(*, product_id: int, color_id: int, size_id: int) -> int:
    return (
        Store.objects.filter(
            product_id=product_id,
            color_id=color_id,
            size_id=size_id,
        )
        .values_list("cnt", flat=True)
        .first()
        or 0
    )


def _build_cart_items(user) -> list[Basket]:
    stock_subquery = Store.objects.filter(
        product_id=OuterRef("product_id"),
        color_id=OuterRef("color_id"),
        size_id=OuterRef("size_id"),
    ).values("cnt")[:1]

    items = (
        Basket.objects.filter(user=user)
        .select_related("product", "product__category", "size", "color")
        .annotate(
            stock_cnt=Coalesce(
                Subquery(stock_subquery, output_field=IntegerField()),
                Value(0),
            )
        )
    )
    items = list(items)
    for item in items:
        item.unit_price = _get_effective_price(item.product)
        item.line_total = item.unit_price * item.quantity
        # Явно прокидываем выбранный цвет/размер в контекст рендера корзины.
        item.color_title = getattr(item.color, "title", "Не указан")
        item.size_value = getattr(item.size, "size", "Не указан")
    return items


def _update_basket_item(request: HttpRequest) -> JsonResponse:
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "Некорректный JSON"},
            status=400,
        )

    basket_id = payload.get("basket_id")
    quantity = payload.get("quantity")

    try:
        basket_id = int(basket_id)
        quantity = int(quantity)
    except (TypeError, ValueError):
        return JsonResponse(
            {"success": False, "error": "basket_id и quantity должны быть числами"},
            status=400,
        )

    item = (
        Basket.objects.filter(id=basket_id, user=request.user)
        .select_related("product")
        .first()
    )
    if item is None:
        return JsonResponse(
            {"success": False, "error": "Позиция корзины не найдена"},
            status=404,
        )

    stock_cnt = _get_stock_count(
        product_id=item.product_id,
        color_id=item.color_id,
        size_id=item.size_id,
    )

    removed = False
    capped = False
    line_total = Decimal("0")

    if quantity <= 0 or stock_cnt <= 0:
        item.delete()
        quantity = 0
        removed = True
    else:
        quantity_in_stock = min(quantity, stock_cnt)
        capped = quantity_in_stock != quantity
        quantity = quantity_in_stock
        if item.quantity != quantity:
            item.quantity = quantity
            item.save(update_fields=["quantity", "updated_at"])
        line_total = _get_effective_price(item.product) * quantity

    cart_total_items, cart_total_price_items = _get_cart_totals(request.user)

    response_data = {
        "success": True,
        "basket_id": basket_id,
        "removed": removed,
        "quantity": quantity,
        "stock_cnt": stock_cnt,
        "line_total": f"{line_total:.2f}",
        "cart_total_items": cart_total_items,
        "cart_total_price_items": f"{cart_total_price_items:.2f}",
        "capped": capped,
    }
    if capped:
        response_data["message"] = f"В наличии только {stock_cnt} шт."

    return JsonResponse(response_data)


@login_required(login_url="login")
def basket(request: HttpRequest) -> HttpResponse:
    if (
        request.method == "POST"
        and request.headers.get("x-requested-with") == "XMLHttpRequest"
    ):
        return _update_basket_item(request)

    items = _build_cart_items(request.user)

    cart_total_items, cart_total_price_items = _get_cart_totals(request.user)

    return render(
        request,
        "basket/basket.html",
        {
            "cart": items,
            "user": request.user,
            "cart_total_items": cart_total_items,
            "cart_total_price_items": cart_total_price_items,
        },
    )


def cart(request, product_id):
    if request.method != "POST" or request.headers.get("x-requested-with") != "XMLHttpRequest":
        return JsonResponse({"success": False, "error": "Метод не поддерживается"}, status=405)

    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Некорректный JSON"}, status=400)

    try:
        requested_qty = int(payload.get("quantity", 1))
    except (TypeError, ValueError):
        return JsonResponse({"success": False, "error": "quantity должен быть числом"}, status=400)
    requested_qty = max(1, requested_qty)
    product = get_object_or_404(Products, id=product_id)

    color_title = str(payload.get("color", "")).strip()
    size_value_raw = str(payload.get("size", "")).strip()
    if not color_title or not size_value_raw:
        session_cart = request.session.get("cart", {})
        product_id_str = str(product_id)
        cart_preview = {
            product_id_str: {
                "id": product.pk,
                "name": product.title,
                "img": f"{product.get_path_image_thumbnail}",
                "price": str(product.price),
                "quantity": 0,
                "slug": product.slug,
            }
        }

        if product_id_str in session_cart:
            session_cart[product_id_str]["quantity"] = requested_qty
        else:
            cart_preview[product_id_str]["quantity"] = requested_qty
            request.session.setdefault("cart", {}).update(cart_preview)

        request.session.modified = True
        return JsonResponse(session_cart.get(product_id_str, cart_preview[product_id_str]))

    if not request.user.is_authenticated:
        login_url = f"{reverse('login')}?next={request.path}"
        return JsonResponse(
            {
                "success": False,
                "auth_required": True,
                "login_url": login_url,
                "error": "Требуется авторизация",
            },
            status=401,
        )
    color = Colors.objects.filter(title=color_title).first()
    if color is None:
        return JsonResponse({"success": False, "error": "Цвет не найден"}, status=400)

    try:
        size_int = int(size_value_raw)
    except (TypeError, ValueError):
        return JsonResponse({"success": False, "error": "Размер должен быть числом"}, status=400)

    size = Sizes.objects.filter(size=size_int).first()
    if size is None:
        return JsonResponse({"success": False, "error": "Размер не найден"}, status=400)

    store_item = (
        Store.objects.filter(product=product, color=color, size=size)
        .values("cnt")
        .first()
    )
    stock_cnt = int(store_item["cnt"]) if store_item else 0
    if stock_cnt <= 0:
        return JsonResponse({"success": False, "error": "Этого варианта нет в наличии"}, status=409)

    capped = False
    item, created = Basket.objects.get_or_create(
        user=request.user,
        product=product,
        color=color,
        size=size,
        defaults={"quantity": min(requested_qty, stock_cnt)},
    )
    if created:
        capped = requested_qty > stock_cnt
    else:
        target_qty = item.quantity + requested_qty
        new_qty = min(target_qty, stock_cnt)
        capped = new_qty != target_qty
        if item.quantity != new_qty:
            item.quantity = new_qty
            item.save(update_fields=["quantity", "updated_at"])

    cart_total_items, cart_total_price_items = _get_cart_totals(request.user)

    response_data = {
        "success": True,
        "in_cart": True,
        "basket_id": item.id,
        "quantity": item.quantity,
        "stock_cnt": stock_cnt,
        "cart_total_items": cart_total_items,
        "cart_total_price_items": f"{cart_total_price_items:.2f}",
        "button_text": "Товар в корзине",
        "capped": capped,
    }
    if capped:
        response_data["message"] = f"В наличии только {stock_cnt} шт."

    return JsonResponse(response_data)
