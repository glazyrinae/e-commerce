from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_items, name='list_items'),
    path('<slug:category_slug>', views.products, name='products'),
]
