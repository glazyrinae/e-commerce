import re

from django import forms
from django.utils import timezone

from .models import Comment


class CommentForm(forms.ModelForm):
    """Простая форма для комментария с рейтингом"""

    # Дополнительное поле для капчи (опционально)
    captcha = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Comment
        fields = ["name", "email", "rating", "text"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ваше имя",
                    "required": "required",
                }
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "Email (необязательно)"}
            ),
            "rating": forms.HiddenInput(),
            "text": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Ваш комментарий...",
                    "maxlength": "2000",
                }
            ),
        }
        labels = {
            "name": "Имя",
            "email": "Email",
            "rating": "Оценка",
            "text": "Комментарий",
        }
        help_texts = {
            "name": "Обязательное поле",
            "email": "Необязательно, используется только для связи",
            "rating": "Выберите от 1 до 5 звезд",
            "text": "Максимум 2000 символов",
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.content_object = kwargs.pop("content_object", None)
        self.user = kwargs.pop("user", None)

        super().__init__(*args, **kwargs)

        # Автозаполнение для авторизованных пользователей
        if self.user and self.user.is_authenticated:
            self.fields["name"].initial = (
                self.user.get_full_name() or self.user.username
            )
            self.fields["email"].initial = self.user.email
            self.fields["name"].widget.attrs["readonly"] = True
            self.fields["email"].widget.attrs["readonly"] = True

    def clean_name(self):
        """Валидация имени"""
        name = self.cleaned_data.get("name", "").strip()

        if not name:
            raise forms.ValidationError("Введите ваше имя")

        if len(name) < 2:
            raise forms.ValidationError("Имя слишком короткое")

        if len(name) > 100:
            raise forms.ValidationError("Имя слишком длинное")

        # Проверка на допустимые символы
        if not re.match(r"^[a-zA-Zа-яА-ЯёЁ\s\-\.]+$", name):
            raise forms.ValidationError("Имя содержит недопустимые символы")

        return name

    def clean_email(self):
        """Валидация email"""
        email = self.cleaned_data.get("email", "").strip()

        if email:
            # Базовая проверка формата
            if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
                raise forms.ValidationError("Введите корректный email адрес")

        return email

    def clean_rating(self):
        """Валидация рейтинга"""
        rating = self.cleaned_data.get("rating", 0)

        if not rating or rating < 1 or rating > 5:
            raise forms.ValidationError("Выберите оценку от 1 до 5 звезд")

        return rating

    def clean_text(self):
        """Валидация текста комментария"""
        text = self.cleaned_data.get("text", "").strip()

        if not text:
            raise forms.ValidationError("Введите текст комментария")

        if len(text) < 10:
            raise forms.ValidationError("Комментарий слишком короткий")

        if len(text) > 2000:
            raise forms.ValidationError("Комментарий слишком длинный")

        # Простая проверка на спам (можно расширить)
        spam_words = ["купить", "цена", "дешево", "http://", "https://"]
        if any(word in text.lower() for word in spam_words):
            self.instance.status = Comment.Status.SPAM

        return text

    def save(self, commit=True):
        comment = super().save(commit=False)

        # Устанавливаем пользователя если авторизован
        if self.user and self.user.is_authenticated:
            comment.user = self.user
            comment.is_anonymous = False

        # Устанавливаем связанный объект
        if self.content_object:
            comment.content_object = self.content_object

        # Сохраняем метаданные запроса
        if self.request:
            comment.ip_address = self.request.META.get("REMOTE_ADDR")
            comment.user_agent = self.request.META.get("HTTP_USER_AGENT", "")[:500]

            # Генерация капчи (если нужно)
            import hashlib

            seed = f"{comment.ip_address}{timezone.now().timestamp()}"
            comment.metadata["captcha_hash"] = hashlib.md5(seed.encode()).hexdigest()[
                :8
            ]

        if commit:
            comment.save()

        return comment


class AdminReplyForm(forms.ModelForm):
    """Форма для ответа администратора"""

    class Meta:
        model = Comment
        fields = ["admin_reply"]
        widgets = {
            "admin_reply": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Ваш ответ пользователю...",
                    "maxlength": "2000",
                }
            ),
        }
        labels = {
            "admin_reply": "Ответ администратора",
        }

    def clean_admin_reply(self):
        reply = self.cleaned_data.get("admin_reply", "").strip()

        if not reply:
            raise forms.ValidationError("Введите текст ответа")

        if len(reply) < 10:
            raise forms.ValidationError("Ответ слишком короткий")

        return reply

    def save(self, commit=True):
        comment = super().save(commit=False)
        comment.replied_at = timezone.now()

        if commit:
            comment.save()

        return comment
