from django.shortcuts import render
import logging

logger = logging.getLogger('products')


def list_items(request):
    return render(request, "items/list_items.html")
