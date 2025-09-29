from django.shortcuts import render, get_object_or_404
from .models import Products
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)


# Главная
def list_items(request):
    products = Products.objects.select_related("category").order_by("?")[:10]
    return render(
        request,
        "items/list_items.html",
        {"featured_products": products[:5], "latest_products": products[5:10]},
    )


def product(request, category_slug, product_id):
    del request.session["cart"]
    product = get_object_or_404(
        Products.objects.select_related("category"),
        category__slug=category_slug,
        id=product_id,
    )
    images = product.images.all()
    store = product.store.all()
    colors = {str(c.color) for c in store if c.color}
    sizes = {str(s.size) for s in store if s.size}
    return render(
        request,
        "detail.html",
        {"product": product, "images": images, "colors": colors, "sizes": sizes},
    )


def products(request, category_slug):
    items_per_page = 5
    page_number = request.GET.get("page", 1)

    products = (
        Products.objects.select_related("category")
        .filter(category__slug=category_slug)
        .order_by("-created_at")
    )
    paginator = Paginator(products, items_per_page)
    page_obj = paginator.get_page(page_number)

    # Проверяем AJAX запрос
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return load_more_content(request, category_slug)

    return render(request, "items/products.html", {"products": page_obj})


# AJAX
def load_modal_content(request, category_slug):
    page_number = request.GET.get("page", 1)
    items_per_page = 5

    products = (
        Products.objects.select_related("category")
        .filter(category__slug=category_slug)
        .order_by("-created_at")
    )

    paginator = Paginator(products, items_per_page)
    page_obj = paginator.get_page(page_number)

    html_content = render_to_string("ajax/items_partial.html", {"products": page_obj})

    return JsonResponse({"html": html_content, "has_next": page_obj.has_next()})


def load_more_content(request, category_slug):
    page_number = request.GET.get("page", 1)
    items_per_page = 5

    products = (
        Products.objects.select_related("category")
        .filter(category__slug=category_slug)
        .order_by("-created_at")
    )

    paginator = Paginator(products, items_per_page)
    page_obj = paginator.get_page(page_number)

    html_content = render_to_string("ajax/items_partial.html", {"products": page_obj})

    return JsonResponse({"html": html_content, "has_next": page_obj.has_next()})
