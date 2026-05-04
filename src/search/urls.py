# search/urls.py
from django.urls import path

from . import views
from .views import get_field_choices

app_name = "search"

urlpatterns = [
    path("", views.api_search, name="search_result"),
    path("api/search/", views.api_search, name="api_search"),
    path(
        "api/field-choices/<int:config_id>/<int:field_id>/",
        get_field_choices,
        name="field_choices",
    ),
]
