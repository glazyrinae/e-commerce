import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone


class Comment(models.Model):
    """
    Универсальная модель комментариев с рейтингом.
    Поддерживает анонимных и авторизованных пользователей.
    """

    # Уникальный идентификатор
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ========== СВЯЗЬ С ОБЪЕКТОМ ==========
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name="Тип объекта",
        help_text="Тип объекта, к которому привязан комментарий",
    )
    object_id = models.PositiveIntegerField(
        verbose_name="ID объекта",
        help_text="ID объекта, к которому привязан комментарий",
    )
    content_object = GenericForeignKey("content_type", "object_id")

    # ========== ПОЛЬЗОВАТЕЛЬ ==========
    # Авторизованный пользователь (может быть NULL)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="comments",
        verbose_name="Пользователь",
        help_text="Авторизованный пользователь (если оставил комментарий)",
    )

    # Имя (обязательно для всех)
    name = models.CharField(
        max_length=100,
        verbose_name="Имя",
        help_text="Имя пользователя, оставившего комментарий",
    )

    # Email (необязательно)
    email = models.EmailField(
        blank=True, verbose_name="Email", help_text="Email пользователя (необязательно)"
    )

    # ========== КОММЕНТАРИЙ И РЕЙТИНГ ==========
    # Текст комментария
    text = models.TextField(
        max_length=2000,
        verbose_name="Комментарий",
        help_text="Текст комментария (максимум 2000 символов)",
    )

    # Рейтинг от 1 до 5
    RATING_CHOICES = [
        (1, "★☆☆☆☆ - Очень плохо"),
        (2, "★★☆☆☆ - Плохо"),
        (3, "★★★☆☆ - Средне"),
        (4, "★★★★☆ - Хорошо"),
        (5, "★★★★★ - Отлично"),
    ]

    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        default=0,
        verbose_name="Рейтинг",
        help_text="Оценка от 1 до 5 звезд",
    )

    # ========== СТАТУС И МОДЕРАЦИЯ ==========
    # Статус комментария
    class Status(models.TextChoices):
        PENDING = "pending", "На модерации"
        APPROVED = "approved", "Одобрено"
        REJECTED = "rejected", "Отклонено"
        SPAM = "spam", "Спам"

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Статус",
        help_text="Статус модерации комментария",
    )

    # Ответ администратора
    admin_reply = models.TextField(
        max_length=2000,
        blank=True,
        verbose_name="Ответ администратора",
        help_text="Ответ администратора на комментарий",
    )

    # ========== МЕТАДАННЫЕ ==========
    # IP адрес
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP адрес",
        help_text="IP адрес пользователя",
    )

    # User Agent
    user_agent = models.TextField(
        blank=True,
        verbose_name="User Agent",
        help_text="Информация о браузере пользователя",
    )

    # ========== ВРЕМЕННЫЕ МЕТКИ ==========
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    # Дата ответа администратора
    replied_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата ответа")

    # ========== ФЛАГИ ==========
    is_edited = models.BooleanField(default=False, verbose_name="Редактировался")
    is_verified = models.BooleanField(default=False, verbose_name="Проверено")
    is_anonymous = models.BooleanField(default=True, verbose_name="Анонимный")

    # ========== ДОПОЛНИТЕЛЬНЫЕ ДАННЫЕ ==========
    # Для будущего расширения
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Метаданные",
        help_text="Дополнительные данные в формате JSON",
    )

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        ordering = ["-created_at"]
        indexes = [
            # Основные индексы для быстрого поиска
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["rating"]),
            models.Index(fields=["status"]),
            models.Index(fields=["user"]),
            models.Index(fields=["email"]),
            models.Index(fields=["is_verified"]),
        ]
        constraints = [
            # Проверка рейтинга
            models.CheckConstraint(
                condition=models.Q(rating__gte=0) & models.Q(rating__lte=5),
                name="rating_range_check",
            ),
        ]

    def __str__(self):
        return f"Комментарий от {self.name} ({self.rating}★)"

    def save(self, *args, **kwargs):
        # Определяем анонимность
        self.is_anonymous = not bool(self.user)

        # Обновляем время ответа
        if self.admin_reply and not self.replied_at:
            self.replied_at = timezone.now()

        super().save(*args, **kwargs)

    # ========== МЕТОДЫ ДЛЯ УДОБСТВА ==========
    def get_display_name(self):
        """Получение отображаемого имени"""
        if self.user:
            return self.user.get_full_name() or self.user.username
        return self.name

    def get_user_type(self):
        """Тип пользователя"""
        if self.user:
            if self.user.is_staff:
                return "staff"
            return "authenticated"
        return "anonymous"

    def has_admin_reply(self):
        """Есть ли ответ администратора"""
        return bool(self.admin_reply.strip())

    def can_edit(self, user):
        """Может ли пользователь редактировать комментарий"""
        if not user.is_authenticated:
            return False
        return user == self.user or user.is_staff

    def can_reply(self, user):
        """Может ли пользователь отвечать на комментарий"""
        return user.is_authenticated and user.is_staff

    def mark_as_verified(self):
        """Пометить как проверенный"""
        self.is_verified = True
        self.save(update_fields=["is_verified", "updated_at"])

    def get_rating_display_stars(self):
        """Отображение рейтинга в виде звезд"""
        stars = "★" * self.rating + "☆" * (5 - self.rating)
        return f"{stars} ({self.rating}/5)"

    # ========== СТАТИСТИЧЕСКИЕ МЕТОДЫ ==========
    @classmethod
    def get_for_object(cls, obj):
        """Получение всех комментариев для объекта"""
        content_type = ContentType.objects.get_for_model(obj)
        return cls.objects.filter(
            content_type=content_type, object_id=obj.pk, status=cls.Status.APPROVED
        )

    @classmethod
    def get_statistics(cls, obj):
        """Статистика комментариев для объекта"""
        comments = cls.get_for_object(obj)

        return {
            "total": comments.count(),
            "average_rating": comments.aggregate(avg=models.Avg("rating"))["avg"] or 0,
            "ratings_distribution": {
                1: comments.filter(rating=1).count(),
                2: comments.filter(rating=2).count(),
                3: comments.filter(rating=3).count(),
                4: comments.filter(rating=4).count(),
                5: comments.filter(rating=5).count(),
            },
            "with_replies": comments.filter(admin_reply__regex=r"\S").count(),
            "verified": comments.filter(is_verified=True).count(),
        }

    # ========== МЕТОДЫ ДЛЯ АДМИНИСТРАТОРА ==========
    def approve(self):
        """Одобрить комментарий"""
        self.status = self.Status.APPROVED
        self.save(update_fields=["status", "updated_at"])

    def reject(self):
        """Отклонить комментарий"""
        self.status = self.Status.REJECTED
        self.save(update_fields=["status", "updated_at"])

    def mark_as_spam(self):
        """Пометить как спам"""
        self.status = self.Status.SPAM
        self.save(update_fields=["status", "updated_at"])


# ========== ПРОКСИ-МОДЕЛИ ДЛЯ УДОБСТВА ==========
class PendingComment(Comment):
    """Прокси-модель для комментариев на модерации"""

    class Meta:
        proxy = True
        verbose_name = "Комментарий на модерации"
        verbose_name_plural = "Комментарии на модерации"

    def save(self, *args, **kwargs):
        # Всегда сохраняем со статусом "на модерации"
        self.status = Comment.Status.PENDING
        super().save(*args, **kwargs)


class ApprovedComment(Comment):
    """Прокси-модель для одобренных комментариев"""

    class Meta:
        proxy = True
        verbose_name = "Одобренный комментарий"
        verbose_name_plural = "Одобренные комментарии"
        default_manager_name = "objects"

    def get_queryset(self):
        return super().get_queryset().filter(status=Comment.Status.APPROVED)


# ========== МЕНЕДЖЕРЫ ДЛЯ УДОБНЫХ ЗАПРОСОВ ==========
class CommentManager(models.Manager):
    """Кастомный менеджер для комментариев"""

    def get_approved(self):
        """Только одобренные комментарии"""
        return self.filter(status=Comment.Status.APPROVED)

    def get_pending(self):
        """Только комментарии на модерации"""
        return self.filter(status=Comment.Status.PENDING)

    def get_for_object(self, obj):
        """Комментарии для конкретного объекта"""
        content_type = ContentType.objects.get_for_model(obj)
        return self.filter(content_type=content_type, object_id=obj.pk)

    def with_replies(self):
        """Комментарии с ответами администратора"""
        return self.filter(admin_reply__regex=r"\S")

    def verified(self):
        """Проверенные комментарии"""
        return self.filter(is_verified=True)

    def by_rating(self, min_rating=1, max_rating=5):
        """Комментарии по рейтингу"""
        return self.filter(rating__gte=min_rating, rating__lte=max_rating)

    def anonymous(self):
        """Анонимные комментарии"""
        return self.filter(is_anonymous=True)

    def authenticated(self):
        """Комментарии авторизованных пользователей"""
        return self.filter(is_anonymous=False)
