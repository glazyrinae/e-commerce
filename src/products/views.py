import logging
from typing import TypedDict

from django.core.paginator import Paginator
from django.http import HttpRequest, JsonResponse
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string

from .models import Images, Products, Store
from basket.models import Basket

logger = logging.getLogger(__name__)


class ProductStoreItem(TypedDict):
    size: str
    cnt: int
    store_id: int


class ProductViewData(TypedDict):
    product: Products
    product_title: str
    product_category: str
    product_total_cnt: int
    store_items: list[Store]
    colors_grouped: dict[str, list[ProductStoreItem]]


# Главная
def list_items(request: HttpRequest) -> HttpResponse:
    products_qs = Products.get_random_with_details(10)  # это QuerySet
    products_list = list(products_qs)  # преобразуем в список
    available_products = get_products(products_list, request)  # теперь типы совпадают
    # Безопасные срезы
    featured = available_products[:5] if available_products else []
    latest = available_products[5:10] if len(available_products) > 5 else []

    return render(
        request,
        "items/list_items.html",
        {
            "featured_products": featured,
            "latest_products": latest,
        },
    )


def get_item(product: Products, request: HttpRequest) -> dict:

    basket_qty_map: dict[tuple[int, int], int] = {}
    basket_rows: list[tuple[int, int, int]] = []
    if request.user.is_authenticated:
        basket_rows = list(
            Basket.objects.filter(
                user_id=request.user.id,
                product_id=product.id,
            ).values_list("color_id", "size_id", "quantity")
        )
        basket_qty_map = {
            (color_id, size_id): qty for color_id, size_id, qty in basket_rows
        }

    store_items = list(
        Store.objects.filter(product=product).select_related("color", "size")
    )
    debug_basket = request.GET.get("debug_basket") == "1"
    if debug_basket:
        store_keys = [(item.color_id, item.size_id, item.cnt) for item in store_items]
        print(
            "[DEBUG_BASKET:get_item]",
            {
                "user_id": getattr(request.user, "id", None),
                "is_authenticated": request.user.is_authenticated,
                "product_id": product.id,
                "basket_rows": basket_rows,
                "basket_qty_map": basket_qty_map,
                "store_keys": store_keys,
            },
        )

    # Группируем store по цветам для шаблона
    colors_grouped: dict[str, list[ProductStoreItem]] = {}
    for item in store_items:
        color = "Без цвета"
        if item.color and hasattr(item.color, "title"):
            color = item.color.title

        if color not in colors_grouped:
            colors_grouped[color] = []

        # Безопасное получение атрибутов
        size_value: str = "Не указан"
        if item.size and hasattr(item.size, "size"):
            size_value = str(item.size.size)

        variant_key = (item.color_id, item.size_id)
        qty_in_basket = basket_qty_map.get(variant_key, 0)
        in_basket = variant_key in basket_qty_map
        final_cnt = max(0, item.cnt - qty_in_basket)

        colors_grouped[color].append(
            {
                "size": size_value,
                "cnt": final_cnt,
                "store_id": item.pk,
                "in_basket": in_basket,
            }
        )
        if debug_basket:
            print(
                "[DEBUG_BASKET:variant]",
                {
                    "product_id": product.id,
                    "variant_key": variant_key,
                    "qty_in_basket": qty_in_basket,
                    "store_cnt": item.cnt,
                    "final_cnt": final_cnt,
                    "in_basket": in_basket,
                },
            )

    # Безопасное получение атрибутов продукта
    product_title = getattr(product, "title", "Без названия")
    category = getattr(product, "category", None)
    slug = getattr(category, "slug", None)
    category_title = getattr(category, "title", "Без категории")
    total_cnt = sum(getattr(item, "cnt", 0) for item in store_items)

    return {
        "product": product,
        "slug": slug,
        "product_title": product_title,
        "product_category": category_title,
        "product_total_cnt": total_cnt,
        "store_items": store_items,
        "colors_grouped": colors_grouped,
    }


def get_products(
    products: list[Products], request: HttpRequest
) -> list[ProductViewData]:
    available_products: list[ProductViewData] = []
    for product in products:
        available_products.append(get_item(product, request))
    return available_products


def products(request: HttpRequest, category_slug: str) -> HttpResponse:
    items_per_page = 3
    page_number = request.GET.get("page", 1)

    products_qs = (
        Products.objects.select_related("category")
        .filter(category__slug=category_slug)
        .order_by("-created_at")
    )
    products_list = list(products_qs)
    available_products = get_products(products_list, request)
    paginator = Paginator(available_products, items_per_page)
    page_obj = paginator.get_page(page_number)

    # Проверяем AJAX запрос
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return load_more_content(request, category_slug)

    return render(request, "items/products.html", {"products": page_obj})


def load_more_content(request: HttpRequest, category_slug: str) -> JsonResponse:
    page_number = request.GET.get("page", 1)
    items_per_page = 3

    products_qs = (
        Products.objects.select_related("category")
        .filter(category__slug=category_slug)
        .order_by("-created_at")
    )

    products_list = list(products_qs)
    available_products = get_products(products_list, request)
    paginator = Paginator(available_products, items_per_page)
    page_obj = paginator.get_page(page_number)

    html_content = render_to_string(
        "items_partial.html",
        {"objects": page_obj},
        request=request,
    )

    return JsonResponse({"html": html_content, "has_next": page_obj.has_next()})


def product(request: HttpRequest, category_slug: str, product_id: int) -> HttpResponse:

    product = get_object_or_404(
        Products.objects.select_related("category"),
        category__slug=category_slug,
        id=product_id,
    )
    item = get_item(product, request)
    # Безопасное получение связанных объектов через менеджеры
    images: list[Images] = list(Images.objects.filter(product=product))
    item.update(
        {
            "images": images,
        }
    )

    return render(request, "detail.html", item)
