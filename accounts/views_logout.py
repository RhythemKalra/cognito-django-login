"""
Logout (Kanishka).

Two things must happen:
1. Clear OUR session (Django forgets the tokens).
2. Send the browser to Cognito's /logout so Cognito also ends its own login session.
   Otherwise clicking Login again would log the user straight back in without a password.
"""
from urllib.parse import urlencode

from django.conf import settings
from django.shortcuts import redirect


def logout(request):
    request.session.flush()
    params = {
        "client_id": settings.COGNITO_CLIENT_ID,
        "logout_uri": settings.COGNITO_LOGOUT_REDIRECT_URI,
    }
    return redirect(f"https://{settings.COGNITO_DOMAIN}/logout?{urlencode(params)}")
