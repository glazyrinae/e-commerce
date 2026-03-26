# from django.conf import settings
# from django.db import models

# class Profile(models.Model):
#     user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     phone = models.CharField(max_length=20, blank=True)
#     address = models.TextField(blank=True)
#     # ... другие поля

#     def __str__(self):
#         return f'Profile {self.user.email}'
