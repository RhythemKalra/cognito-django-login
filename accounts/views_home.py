"""Home page (Rhythem). Shows a Login button, or a link to Welcome if already logged in."""
from django.shortcuts import render


def home(request):
    logged_in = "id_token" in request.session
    return render(request, "home.html", {"logged_in": logged_in})
