from django.urls import path

from .views_home import home
from .views_login import callback, login

urlpatterns = [
    path("", home, name="home"),            # Rhythem
    path("login/", login, name="login"),     # Bhoomi
    path("callback/", callback, name="callback"),  # Bhoomi
]
