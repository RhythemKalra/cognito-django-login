from django.urls import path

from .views_home import home
from .views_login import callback, login
from .views_logout import logout
from .views_tamper import tamper_test
from .views_welcome import welcome

urlpatterns = [
    path("", home, name="home"),            # Rhythem
    path("login/", login, name="login"),     # Bhoomi
    path("callback/", callback, name="callback"),  # Bhoomi
    path("welcome/", welcome, name="welcome"),     # Krati
    path("tamper-test/", tamper_test, name="tamper_test"),  # Krati
    path("logout/", logout, name="logout"),        # Kanishka
]
