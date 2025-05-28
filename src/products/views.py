from django.shortcuts import render, get_object_or_404
from .models import Products
import logging

logger = logging.getLogger('products')


def list_items(request):
    return render(request, "items/list_items.html")

def products(request, category_slug):
    category = get_object_or_404(Products, gender=category_slug)
    return render(request, 'items/products.html', {'category': category})