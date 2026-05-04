import json
import logging

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_POST, require_GET

from .exceptions import InvalidSearchRequestError, SearchConfigNotFoundError
from .forms import SearchRequestForm
from .services import SearchService
from .field_choices import FieldChoices
from .models import SearchField  # для отлова DoesNotExist

logger = logging.getLogger(__name__)


@require_POST
def api_search(request: HttpRequest) -> JsonResponse:
    """
    API-эндпоинт для поиска товаров.
    Принимает JSON, валидирует через Django Form, вызывает сервис, возвращает HTML-блоки.
    """
    # 1. Парсинг входящего JSON
    try:
        payload = json.loads(request.body)
        if not isinstance(payload, dict):
            raise ValueError("Ожидается JSON-объект")
    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "message": "Некорректный JSON"}, status=400
        )

    # 2. Валидация и нормализация (стандартные средства Django)
    form = SearchRequestForm(data=payload)
    if not form.is_valid():
        return JsonResponse(
            {
                "success": False,
                "message": "Ошибка валидации параметров",
                "errors": form.errors.get_json_data(),
            },
            status=400,
        )

    # 3. Вызов бизнес-логики
    try:
        # cleaned_data уже содержит приведённые типы, нормализованные строки и fallback-значения
        service = SearchService(request)
        service_data = dict(form.cleaned_data)
        service_data.pop("limit", None)
        result = service.execute(**service_data)
        return JsonResponse(result)

    except SearchConfigNotFoundError:
        return JsonResponse(
            {"success": False, "message": "Конфигурация поиска не найдена"}, status=404
        )
    except InvalidSearchRequestError as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)
    except Exception:
        logger.exception("Unexpected error in api_search")
        return JsonResponse(
            {"success": False, "message": "Внутренняя ошибка сервера"}, status=500
        )


@require_GET
def get_field_choices(
    request: HttpRequest, config_id: int, field_id: int
) -> JsonResponse:
    """API-эндпоинт получения вариантов для фильтра поиска."""
    try:
        service = FieldChoices(config_id=config_id, field_id=field_id)
        result = service.get_choices()
        return JsonResponse({"success": True, **result})
    except SearchField.DoesNotExist:
        return JsonResponse(
            {"success": False, "message": "Поле поиска не найдено"}, status=404
        )
    except (ValueError, Exception) as e:
        # В продакшене лучше ловить ValueError и Exception раздельно
        logger.exception("get_field_choices failed")
        return JsonResponse(
            {"success": False, "message": "Ошибка получения вариантов"}, status=500
        )
