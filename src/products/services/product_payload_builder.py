from __future__ import annotations

from typing import Any

from django.http import HttpRequest

from basket.models import Basket
from products.models import Products, Store


class ProductPayloadBuilder:
    """Builds product payloads used by product cards and quick view templates."""

    def __init__(self, request: HttpRequest):
        self.request = request
        self._store_by_product: dict[int, list[Store]] = {}
        self._basket_qty_map: dict[tuple[int, int | None, int | None], int] = {}

    def _prepare(self, product_ids: list[int]) -> None:
        if not product_ids:
            self._store_by_product = {}
            self._basket_qty_map = {}
            return

        unique_ids = list(dict.fromkeys(product_ids))

        self._store_by_product = {product_id: [] for product_id in unique_ids}
        store_items = Store.objects.filter(product_id__in=unique_ids).select_related(
            "color", "size"
        )
        for item in store_items:
            self._store_by_product.setdefault(item.product_id, []).append(item)

        self._basket_qty_map = {}
        user = getattr(self.request, "user", None)
        if user is None or not getattr(user, "is_authenticated", False):
            return

        basket_rows = Basket.objects.filter(
            user_id=user.id,
            product_id__in=unique_ids,
        ).values_list("product_id", "color_id", "size_id", "quantity")

        self._basket_qty_map = {
            (product_id, color_id, size_id): quantity
            for product_id, color_id, size_id, quantity in basket_rows
        }

    def _build_payload_for_product(self, product: Products) -> dict[str, Any]:
        product_id = int(product.pk)
        store_items = self._store_by_product.get(product_id, [])

        colors_grouped: dict[str, list[dict[str, Any]]] = {}
        total_cnt = 0

        for item in store_items:
            color_name = "Без цвета"
            if item.color and hasattr(item.color, "title"):
                color_name = str(item.color.title)

            size_value = "Не указан"
            if item.size and hasattr(item.size, "size"):
                size_value = str(item.size.size)

            basket_key = (product_id, item.color_id, item.size_id)
            qty_in_basket = self._basket_qty_map.get(basket_key, 0)
            in_basket = basket_key in self._basket_qty_map

            store_cnt = int(getattr(item, "cnt", 0) or 0)
            total_cnt += store_cnt
            final_cnt = max(0, store_cnt - qty_in_basket)

            colors_grouped.setdefault(color_name, []).append(
                {
                    "size": size_value,
                    "cnt": final_cnt,
                    "store_id": item.pk,
                    "in_basket": in_basket,
                }
            )

        category = getattr(product, "category", None)
        slug = getattr(category, "slug", None)
        category_title = getattr(category, "title", "")

        return {
            "product": product,
            "slug": slug,
            "product_title": getattr(product, "title", ""),
            "product_category": category_title,
            "product_total_cnt": total_cnt,
            "store_items": store_items,
            "colors_grouped": colors_grouped,
        }

    def build(self, product: Products) -> dict[str, Any]:
        if product.pk is None:
            return {
                "product": product,
                "slug": None,
                "product_title": getattr(product, "title", ""),
                "product_category": "",
                "product_total_cnt": 0,
                "store_items": [],
                "colors_grouped": {},
            }

        self._prepare([int(product.pk)])
        return self._build_payload_for_product(product)

    def build_many(self, products: list[Products] | Any) -> list[dict[str, Any]]:
        product_list = list(products)
        product_ids = [int(product.pk) for product in product_list if product.pk is not None]
        self._prepare(product_ids)

        payloads: list[dict[str, Any]] = []
        for product in product_list:
            if product.pk is None:
                continue
            payloads.append(self._build_payload_for_product(product))
        return payloads
