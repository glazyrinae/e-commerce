from __future__ import annotations

from collections.abc import Iterable

from django.http import HttpRequest
from django.template.loader import render_to_string


class SearchRenderer:
    """Отвечает исключительно за генерацию HTML-фрагментов."""

    def __init__(self, request: HttpRequest):
        self.request = request

    def render_cards(self, payloads: Iterable[dict]) -> str:
        html_chunks = []
        for payload in payloads:
            if payload.get("slug"):
                html_chunks.append(
                    render_to_string(
                        "modals/_product_card.html",
                        {"object": payload},
                        request=self.request,
                    )
                )
        return "".join(html_chunks)

    def render_quick_view(self, payloads: Iterable[dict]) -> str:
        valid = [p for p in payloads if p.get("slug")]
        return str(
            render_to_string(
                "modals/_quick_view.html", {"objects": valid}, request=self.request
            )
        )
