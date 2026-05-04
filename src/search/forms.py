from django import forms


class SearchRequestForm(forms.Form):
    config_id = forms.IntegerField(
        min_value=1,
        error_messages={"min_value": "config_id обязателен и должен быть > 0"},
    )
    content_type_id = forms.IntegerField(
        min_value=1,
        error_messages={"min_value": "content_type_id обязателен и должен быть > 0"},
    )
    category_slug = forms.CharField(required=False, strip=True)
    order_by = forms.CharField(required=False, strip=True)
    page = forms.IntegerField(min_value=1, initial=1)
    per_page = forms.IntegerField(required=False, min_value=1, max_value=100)
    limit = forms.IntegerField(
        required=False, min_value=1, max_value=100
    )  # legacy fallback
    search_data = forms.JSONField(required=False)  # Django 3.2+

    def clean(self):
        cleaned_data = super().clean()

        # Fallback: per_page → limit → 20
        if cleaned_data.get("per_page") is None:
            cleaned_data["per_page"] = cleaned_data.get("limit", 20)

        # Нормализация search_data: гарантируем dict со строковыми ключами
        raw_sd = cleaned_data.get("search_data")
        cleaned_data["search_data"] = {
            str(k): v for k, v in (raw_sd.items() if isinstance(raw_sd, dict) else {})
        }
        return cleaned_data
