from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import View

from .forms import AdminReplyForm, CommentForm
from .models import Comment


class CommentListView(View):
    """Получение списка комментариев с пагинацией"""

    def get(self, request, content_type_id, object_id):
        content_type = get_object_or_404(ContentType, id=content_type_id)

        # Параметры
        page = int(request.GET.get("page", 1))
        per_page = int(request.GET.get("per_page", 10))
        sort_by = request.GET.get("sort", "newest")
        filter_by = request.GET.get("filter", "all")

        # Базовый QuerySet
        comments = Comment.objects.filter(
            content_type=content_type,
            object_id=object_id,
            status=Comment.Status.APPROVED,  # Только одобренные
        ).select_related("user")

        # Фильтрация
        if filter_by == "with_replies":
            comments = comments.filter(admin_reply__regex=r"\S")
        elif filter_by == "verified":
            comments = comments.filter(is_verified=True)
        elif filter_by == "high_rating":
            comments = comments.filter(rating__gte=4)

        # Сортировка
        sort_map = {
            "newest": "-created_at",
            "oldest": "created_at",
            "highest": "-rating",
            "lowest": "rating",
            "replied": "-replied_at",
        }

        order_by = sort_map.get(sort_by, "-created_at")
        comments = comments.order_by(order_by)

        # Пагинация
        paginator = Paginator(comments, per_page)

        try:
            page_obj = paginator.page(page)
        except (PageNotAnInteger, EmptyPage):
            return JsonResponse(
                {"success": False, "error": "Страница не найдена"}, status=404
            )

        # Форматирование данных
        comments_data = []
        for comment in page_obj:
            comments_data.append(
                {
                    "id": str(comment.id),
                    "name": comment.get_display_name(),
                    "email": comment.email,
                    "text": comment.text,
                    "rating": comment.rating,
                    "rating_display": comment.get_rating_display(),
                    "created_at": comment.created_at.strftime("%d.%m.%Y %H:%M"),
                    "is_anonymous": comment.is_anonymous,
                    "is_verified": comment.is_verified,
                    "has_admin_reply": comment.has_admin_reply(),
                    "admin_reply": (
                        comment.admin_reply if comment.has_admin_reply() else None
                    ),
                    "replied_at": (
                        comment.replied_at.strftime("%d.%m.%Y %H:%M")
                        if comment.replied_at
                        else None
                    ),
                    "user_type": comment.get_user_type(),
                    "can_reply": (
                        comment.can_reply(request.user)
                        if request.user.is_authenticated
                        else False
                    ),
                }
            )
        content_object = content_type.get_object_for_this_type(pk=object_id)
        # Статистика
        stats = Comment.get_statistics(content_object)

        # Проверка пользователя
        user_comment = None
        user_filter = self.get_user_filter(request)

        if user_filter:
            user_comment_qs = (
                Comment.objects.filter(
                    content_type=content_type,
                    object_id=object_id,
                )
                .filter(user_filter)
                .first()
            )

            if user_comment_qs:
                user_comment = {
                    "id": str(user_comment_qs.id),
                    "rating": user_comment_qs.rating,
                    "text": user_comment_qs.text,
                    "status": user_comment_qs.get_status_display(),
                    "has_admin_reply": user_comment_qs.has_admin_reply(),
                    "admin_reply": user_comment_qs.admin_reply,
                }

        return JsonResponse(
            {
                "success": True,
                "comments": comments_data,
                "pagination": {
                    "current_page": page_obj.number,
                    "total_pages": paginator.num_pages,
                    "total_items": paginator.count,
                    "has_next": page_obj.has_next(),
                    "has_previous": page_obj.has_previous(),
                },
                "statistics": stats,
                "user_comment": user_comment,
                "sort_by": sort_by,
                "filter_by": filter_by,
                "is_staff": request.user.is_authenticated and request.user.is_staff,
            }
        )

    def get_user_filter(self, request):
        """Фильтр для поиска комментариев пользователя"""
        if request.user.is_authenticated:
            return Q(user=request.user)
        return Q()


class SubmitCommentView(View):
    """Отправка нового комментария"""

    def post(self, request, content_type_id, object_id):
        content_type = get_object_or_404(ContentType, id=content_type_id)

        try:
            content_object = content_type.get_object_for_this_type(pk=object_id)
        except ObjectDoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Объект не найден"}, status=404
            )

        # Проверка частоты отправки
        from datetime import timedelta

        from django.utils import timezone

        recent_limit = timezone.now() - timedelta(hours=1)
        ip = request.META.get("REMOTE_ADDR")

        recent_comments = Comment.objects.filter(
            ip_address=ip, created_at__gte=recent_limit
        ).count()

        if recent_comments >= 3:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Слишком много комментариев за последний час",
                },
                status=429,
            )

        # Обработка формы
        form = CommentForm(
            request.POST,
            request=request,
            content_object=content_object,
            user=request.user,
        )

        if form.is_valid():
            comment = form.save()

            # Авто-одобрение для авторизованных пользователей
            if request.user.is_authenticated:
                comment.approve()

            return JsonResponse(
                {
                    "success": True,
                    "message": "Комментарий отправлен на модерацию",
                    "comment": {
                        "id": str(comment.id),
                        "name": comment.get_display_name(),
                        "rating": comment.rating,
                        "text": comment.text,
                        "status": comment.get_status_display(),
                        "created_at": comment.created_at.strftime("%d.%m.%Y %H:%M"),
                    },
                    "requires_moderation": comment.status == Comment.Status.PENDING,
                }
            )

        return JsonResponse({"success": False, "errors": form.errors}, status=400)


@method_decorator(login_required, name="dispatch")
class AdminCommentView(View):
    """Административные функции для комментариев"""

    def check_permissions(self, request):
        """Проверка прав администратора"""
        return request.user.is_authenticated and request.user.is_staff

    def post(self, request, comment_id):
        """Обработка административных действий"""
        if not self.check_permissions(request):
            return JsonResponse(
                {"success": False, "error": "Требуются права администратора"},
                status=403,
            )

        comment = get_object_or_404(Comment, id=comment_id)
        action = request.POST.get("action")

        if action == "reply":
            return self.handle_reply(request, comment)
        elif action == "approve":
            return self.handle_approve(comment)
        elif action == "reject":
            return self.handle_reject(comment)
        elif action == "verify":
            return self.handle_verify(comment)
        else:
            return JsonResponse(
                {"success": False, "error": "Неизвестное действие"}, status=400
            )

    def handle_reply(self, request, comment):
        """Обработка ответа администратора"""
        form = AdminReplyForm(request.POST, instance=comment)

        if form.is_valid():
            comment = form.save()

            return JsonResponse(
                {
                    "success": True,
                    "message": "Ответ сохранен",
                    "comment": {
                        "id": str(comment.id),
                        "admin_reply": comment.admin_reply,
                        "replied_at": (
                            comment.replied_at.strftime("%d.%m.%Y %H:%M")
                            if comment.replied_at
                            else None
                        ),
                    },
                }
            )

        return JsonResponse({"success": False, "errors": form.errors})

    def handle_approve(self, comment):
        """Одобрение комментария"""
        comment.approve()

        content_object = comment.content_type.get_object_for_this_type(
            pk=comment.object_id
        )
        content_object.rating = comment.get_statistics.get("average_rating", 0)
        content_object.save(update_fields=["rating"])

        return JsonResponse(
            {
                "success": True,
                "message": "Комментарий одобрен",
                "comment": {
                    "id": str(comment.id),
                    "status": comment.get_status_display(),
                },
            }
        )

    def handle_reject(self, comment):
        """Отклонение комментария"""
        comment.reject()

        return JsonResponse(
            {
                "success": True,
                "message": "Комментарий отклонен",
                "comment": {
                    "id": str(comment.id),
                    "status": comment.get_status_display(),
                },
            }
        )

    def handle_verify(self, comment):
        """Верификация комментария"""
        comment.mark_as_verified()

        return JsonResponse(
            {
                "success": True,
                "message": "Комментарий проверен",
                "comment": {
                    "id": str(comment.id),
                    "is_verified": comment.is_verified,
                },
            }
        )


class StatisticsView(View):
    """Получение статистики комментариев"""

    def get(self, request, content_type_id, object_id):
        content_type = get_object_or_404(ContentType, id=content_type_id)

        try:
            content_object = content_type.get_object_for_this_type(pk=object_id)
        except ObjectDoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Объект не найден"}, status=404
            )

        stats = Comment.get_statistics(content_object)

        return JsonResponse({"success": True, "statistics": stats})
