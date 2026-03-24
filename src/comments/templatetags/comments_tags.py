from django import template
from django.contrib.contenttypes.models import ContentType

from ..models import Comment

register = template.Library()


@register.inclusion_tag("comments/widget.html", takes_context=True)
def comments_widget(context, obj, show_form=True, show_stats=True):
    """
    Вставка виджета комментариев в шаблон.

    Использование:
    {% comments_widget object show_form=True show_stats=True %}
    """
    request = context.get("request")

    # Получаем статистику
    stats = Comment.get_statistics(obj) if obj else {}

    # Проверяем комментарий текущего пользователя
    user_comment = None
    if request and request.user.is_authenticated:
        user_comment = Comment.objects.filter(
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.pk,
            user=request.user,
        ).first()

    return {
        "object": obj,
        "stats": stats,
        "user_comment": user_comment,
        "show_form": show_form,
        "show_stats": show_stats,
        "request": request,
        "content_type_id": ContentType.objects.get_for_model(obj).id,
        "object_id": obj.pk,
        "is_staff": (
            request.user.is_authenticated and request.user.is_staff
            if request
            else False
        ),
    }


@register.simple_tag(takes_context=True)
def get_comments_count(context, obj, status="approved"):
    """
    Получение количества комментариев.

    Использование:
    {% get_comments_count product 'approved' as count %}
    """
    if not obj:
        return 0

    comments = Comment.get_for_object(obj)

    if status == "approved":
        comments = comments.filter(status=Comment.Status.APPROVED)
    elif status == "pending":
        comments = comments.filter(status=Comment.Status.PENDING)

    return comments.count()


@register.simple_tag
def average_rating(obj):
    """Средний рейтинг объекта"""
    if not obj:
        return 0

    stats = Comment.get_statistics(obj)
    return round(stats.get("average_rating", 0), 1)


@register.filter
def format_rating(rating):
    """Форматирование рейтинга в звезды"""
    stars = "★" * rating + "☆" * (5 - rating)
    return f"{stars} ({rating}/5)"
