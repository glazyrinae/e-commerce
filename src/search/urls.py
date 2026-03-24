# search/urls.py
from django.urls import path

from . import views

app_name = "search"

urlpatterns = [
    path("", views.ListItems.as_view(), name="search_result"),
    path("api/search/", views.api_search, name="api_search"),
    path(
        "api/field-choices/<int:config_id>/<int:field_id>/",
        views.get_field_choices,
        name="field_choices",
    ),
]
