from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_items, name='list_items'),
    path('<slug:category_slug>/', views.products, name='products'),
    path('<slug:category_slug>/<int:product_id>', views.product, name='product'),
    path('load-more/<slug:category_slug>/', views.load_more_content, name='load_more_content'),
	path('load-modal-product/<int:product_id>', views.load_modal_content, name='load_modal_content'),
]
