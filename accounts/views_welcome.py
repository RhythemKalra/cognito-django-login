"""Welcome page (Krati). Only reachable with a valid, verified ID token."""
from datetime import datetime, timezone

import jwt
from django.shortcuts import redirect, render

from .jwt_utils import verify_id_token


def welcome(request):
    token = request.session.get("id_token")
    if not token:
        return redirect("home")

    try:
        claims = verify_id_token(token)
    except jwt.PyJWTError:
        # expired or tampered token -> clear session and send to home
        request.session.flush()
        return redirect("home")

    context = {
        "name": claims.get("name") or claims.get("email", "").split("@")[0],
        "email": claims.get("email"),
        "user_id": claims.get("sub"),
        "expires": datetime.fromtimestamp(claims["exp"], tz=timezone.utc).astimezone().strftime("%d %b %Y, %I:%M %p"),
        "claims": {k: claims[k] for k in ("sub", "email", "email_verified", "iss", "aud", "token_use", "iat", "exp") if k in claims},
    }
    return render(request, "welcome.html", context)
