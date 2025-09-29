from django.urls import path
from . import views

urlpatterns = [
    path("", views.basket, name="basket"),
    path("cart/<int:product_id>", views.cart, name="cart"),
]
