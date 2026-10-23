from django.urls import path

from .views_home import home

urlpatterns = [
    path("", home, name="home"),            # Rhythem
]
