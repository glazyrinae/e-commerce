from django.contrib import admin
from django.utils.html import format_html

from .models import ApprovedComment, Comment, PendingComment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "rating_stars",
        "text_preview",
        "content_object_link",
        "status_badge",
        "is_verified_badge",
        "created_at",
    )
    list_filter = (
        "rating",
        "status",
        "is_verified",
        "is_anonymous",
        "created_at",
        "content_type",
    )
    search_fields = ("name", "email", "text", "admin_reply")
    readonly_fields = ("id", "created_at", "updated_at", "ip_address")
    fieldsets = (
        (
            "Основная информация",
            {"fields": ("content_type", "object_id", "rating", "text")},
        ),
        (
            "Пользователь",
            {"fields": ("user", "name", "email", "is_anonymous", "is_verified")},
        ),
        ("Модерация", {"fields": ("status", "admin_reply", "replied_at")}),
        ("Метаданные", {"fields": ("ip_address", "user_agent", "metadata")}),
        ("Системное", {"fields": ("id", "created_at", "updated_at")}),
    )

    actions = [
        "approve_comments",
        "reject_comments",
        "mark_as_verified",
        "mark_as_spam",
    ]

    @admin.display(description="Рейтинг")
    def rating_stars(self, obj):
        return format_html(
            '<span style="color: #ffc107; font-size: 1.2em;">{}</span>',
            "★" * obj.rating + "☆" * (5 - obj.rating),
        )

    @admin.display(description="Комментарий")
    def text_preview(self, obj):
        preview = obj.text[:50]
        if len(obj.text) > 50:
            preview += "..."
        return preview

    @admin.display(description="Объект")
    def content_object_link(self, obj):
        if obj.content_object and hasattr(obj.content_object, "get_absolute_url"):
            return format_html(
                '<a href="{}">{}</a>',
                obj.content_object.get_absolute_url(),
                str(obj.content_object),
            )
        return str(obj.content_object)

    @admin.display(description="Статус")
    def status_badge(self, obj):
        colors = {
            "pending": "warning",
            "approved": "success",
            "rejected": "danger",
            "spam": "dark",
        }
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            colors.get(obj.status, "secondary"),
            obj.get_status_display(),
        )

    @admin.display(description="Проверка")
    def is_verified_badge(self, obj):
        if obj.is_verified:
            return format_html('<span class="badge bg-success">✓ Проверено</span>')
        return format_html('<span class="badge bg-secondary">Не проверено</span>')

    @admin.action(description="Одобрить выбранные")
    def approve_comments(self, request, queryset):
        updated = queryset.update(status=Comment.Status.APPROVED)
        self.message_user(request, f"{updated} комментариев одобрено")

    @admin.action(description="Отклонить выбранные")
    def reject_comments(self, request, queryset):
        updated = queryset.update(status=Comment.Status.REJECTED)
        self.message_user(request, f"{updated} комментариев отклонено")

    @admin.action(description="Пометить как проверенные")
    def mark_as_verified(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f"{updated} комментариев проверено")

    @admin.action(description="Пометить как спам")
    def mark_as_spam(self, request, queryset):
        updated = queryset.update(status=Comment.Status.SPAM)
        self.message_user(request, f"{updated} комментариев помечено как спам")


@admin.register(PendingComment)
class PendingCommentAdmin(CommentAdmin):
    """Админка для комментариев на модерации"""

    def get_queryset(self, request):
        return super().get_queryset(request).filter(status=Comment.Status.PENDING)

    def has_add_permission(self, request):
        return False


@admin.register(ApprovedComment)
class ApprovedCommentAdmin(CommentAdmin):
    """Админка для одобренных комментариев"""

    def get_queryset(self, request):
        return super().get_queryset(request).filter(status=Comment.Status.APPROVED)
