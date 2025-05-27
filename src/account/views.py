from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth import authenticate, login
from .forms import LoginForm, UserRegistrationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings 
from django.shortcuts import redirect
from django.utils.encoding import force_str
from django.contrib.auth.models import User
import logging

logger = logging.getLogger('account')

def send_activation_email(user, request):
    # Генерация токена и uid
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Создание ссылки активации
    activation_link = f"{request.scheme}://{request.get_host()}/account/activate/{uid}/{token}/"
    
    # Формирование письма
    subject = 'Активация аккаунта'
    message = render_to_string('account/activation_email.html', {
        'user': user,
        'activation_link': activation_link,
    })
    
    # Отправка письма
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=message,
        fail_silently=False,
    )

def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        #login(request, user)
        return render(request, "account/account_activated.html")
    else:
        return render(request, "account/activation_invalid.html")

def user_login(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(
                request, username=cd["username"], password=cd["password"]
            )
            if user is not None:
                if user.is_active:
                    login(request, user)
                    logger.info(f'Пользователь {user} успешно авторизован')
                    return HttpResponse("Authenticated successfully")
            else:
                return HttpResponse("Disabled account")
        else:
            return HttpResponse("Invalid login")
    else:
        form = LoginForm()
        return render(request, "account/login.html", {"form": form})


def register(request):
    if request.method == "POST":
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.set_password(user_form.cleaned_data["password"])
            new_user.save()
            send_activation_email(new_user, request)
            return render(request, "account/registration_send_email_done.html")
    else:
        user_form = UserRegistrationForm(instance=None)
    return render(request, "account/register.html", {"user_form": user_form})


@login_required
def dashboard(request):
    return render(request, "account/dashboard.html", {"section": "dashboard"})
