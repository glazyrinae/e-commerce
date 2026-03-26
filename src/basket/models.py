from django.conf import settings
from django.db import models

from products.models import Colors, Products, Sizes


class Basket(models.Model):
    """
    Позиция товара в корзине пользователя.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="basket_items",
        verbose_name="Пользователь",
        help_text="Пользователь, которому принадлежит позиция корзины",
        db_comment="Внешний ключ на пользователя",
    )

    product = models.ForeignKey(
        Products,
        on_delete=models.CASCADE,
        related_name="basket_items",
        verbose_name="Товар",
        help_text="Товар в корзине",
        db_comment="Внешний ключ на таблицу Products",
    )

    size = models.ForeignKey(
        Sizes,
        on_delete=models.CASCADE,
        related_name="basket_items",
        verbose_name="Размер товара",
        help_text="Выбранный размер товара",
        db_comment="Внешний ключ на таблицу Sizes",
    )

    color = models.ForeignKey(
        Colors,
        on_delete=models.CASCADE,
        related_name="basket_items",
        verbose_name="Цвет товара",
        help_text="Выбранный цвет товара",
        db_comment="Внешний ключ на таблицу Colors",
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="Количество",
        help_text="Количество единиц товара в корзине",
        db_comment="Количество единиц товара в позиции корзины",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Создано",
        help_text="Дата и время создания позиции",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Обновлено",
        help_text="Дата и время последнего изменения позиции",
    )

    class Meta:
        ordering = ["-updated_at", "-id"]
        indexes = [
            models.Index(fields=["user"], name="basket_user_idx"),
            models.Index(fields=["user", "product"], name="basket_user_product_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product", "size", "color"],
                name="basket_user_product_size_color_uniq",
            )
        ]
        verbose_name = "Позиция корзины"
        verbose_name_plural = "Позиции корзины"
        db_table_comment = "Позиции товаров в корзине пользователей"

    def __str__(self) -> str:
        return (
            f"Basket(user={self.user_id}, product={self.product_id}, "
            f"size={self.size_id}, color={self.color_id}, qty={self.quantity})"
        )
