from django.core.paginator import Paginator
from django.http import HttpRequest, JsonResponse
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string

from .models import Images, Products
from .services import ProductPayloadBuilder


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
    return ProductPayloadBuilder(request).build(product)


def get_products(
    products: list[Products], request: HttpRequest
) -> list[dict]:
    return ProductPayloadBuilder(request).build_many(products)


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
