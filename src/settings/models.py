from django.db import models
from django.utils.translation import gettext_lazy as _

class Settings(models.Model):
    title = models.CharField(_('Название сайта'), max_length=100)
    site_logo = models.ImageField(_('Логотип'), upload_to='site_settings/', null=True, blank=True)
    footer_text = models.TextField(_('Текст в подвале'), blank=True)
    phone_number = models.CharField(_('Телефон'), max_length=20, blank=True)
    email = models.EmailField(_('Email'), blank=True)
    is_maintenance_mode = models.BooleanField(_('Режим обслуживания'), default=False)

    class Meta:
        verbose_name = _('Настройка сайта')
        verbose_name_plural = _('Настройки сайта')

    def __str__(self):
        return self.title

class MenuItem(models.Model):
    title = models.CharField(_('Название'), max_length=50)
    url = models.CharField(_('URL'), max_length=200)
    order = models.PositiveIntegerField(_('Порядок'), default=0)
    is_active = models.BooleanField(_('Активно'), default=True)

    class Meta:
        verbose_name = _('Пункт меню')
        verbose_name_plural = _('Пункты меню')
        ordering = ['order']

    def __str__(self):
        return self.title
