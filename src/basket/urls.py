from django.urls import path
from . import views

urlpatterns = [
    path('products', views.basket, name='basket')
]
