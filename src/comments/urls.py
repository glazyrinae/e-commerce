from django.urls import path

from . import views

app_name = "comments"

urlpatterns = [
    # Публичные эндпоинты
    path(
        "list/<int:content_type_id>/<int:object_id>/",
        views.CommentListView.as_view(),
        name="list",
    ),
    path(
        "submit/<int:content_type_id>/<int:object_id>/",
        views.SubmitCommentView.as_view(),
        name="submit",
    ),
    path(
        "stats/<int:content_type_id>/<int:object_id>/",
        views.StatisticsView.as_view(),
        name="stats",
    ),
    # Административные эндпоинты
    # path(
    #     "admin/<uuid:comment_id>/",
    #     views.AdminCommentView.as_view(),
    #     name="admin_action",
    # ),
]
