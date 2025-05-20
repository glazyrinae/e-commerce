from django.shortcuts import render


def list_items(request):
    return render(request, "items/list_items.html")
