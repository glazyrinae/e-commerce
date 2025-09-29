from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from products.models import Products
from django.conf import settings
import logging
import json

logger = logging.getLogger(__name__)


# Главная
def basket(request):
    cart = request.session.get("cart", {})
    return render(
        request,
        "basket/basket.html",
        {
            "cart": cart,
            "cart_total_items": get_cart_total_items(cart),
            "cart_total_price_items": get_cart_total_price_items(cart),
        },
    )


def cart(request, product_id):

    product = get_object_or_404(Products, id=product_id)
    # del request.session["cart"]
    cart = request.session.get("cart", {})
    product_id_str = str(product_id)
    cart_preview = {
        product_id_str: {
            "id": product.id,
            "name": product.title,
            "img": f"{settings.MEDIA_URL}{product.get_path_image_thumbnail}",
            "price": str(product.price),
            "quantity": 0,
            "slug": product.slug,
        }
    }
    print("---")
    print(cart)
    print("+++")
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        if request.method == "POST":
            if request.body:
                data = json.loads(request.body)  # Нужно парсить из request.body
                quantity = data.get("quantity")
                if product_id_str in cart:
                    if int(quantity) == 0:
                        del request.session["cart"][product_id_str]
                    else:
                        cart[product_id_str]["quantity"] = quantity
                else:
                    cart_preview[product_id_str]["quantity"] = quantity
                    request.session["cart"].update(cart_preview)
                    logger.info(f'Товар "{product_id_str}" добавлен с {quantity}')
            logger.info(f'Товар "{product.title}" добавлен в корзину')
        request.session.modified = True
        return JsonResponse(cart.get(product_id_str, cart_preview[product_id_str]))

    return render(
        request,
        "basket/basket.html",
        {
            "success": True,
            "product": cart,
            "cart_total_items": get_cart_total_items(cart),
            "cart_total_price_items": get_cart_total_price_items(cart),
        },
    )


def get_cart_total_items(cart):
    """Вспомогательная функция для подсчета общего количества товаров"""
    return sum(item["quantity"] for item in cart.values())


def get_cart_total_price_items(cart):
    """Вспомогательная функция для подсчета суммы общего количества товаров"""
    return sum(float(item["price"]) for item in cart.values())
