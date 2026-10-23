"""
Login flow (Bhumi).

Step 1  /login/    -> we redirect the browser to Cognito's Hosted UI.
Step 2  user logs in on Cognito's page (we never see the password).
Step 3  /callback/ -> Cognito sends the browser back here with ?code=...&state=...
Step 4  we exchange that one-time code for tokens (server to server).
"""
import secrets
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect


def login(request):
    # 'state' is a random value we remember. Cognito sends it back unchanged,
    # so we can check the callback really came from the login WE started (stops CSRF).
    state = secrets.token_urlsafe(16)
    request.session["oauth_state"] = state

    params = {
        "response_type": "code",            # Authorization Code flow
        "client_id": settings.COGNITO_CLIENT_ID,
        "redirect_uri": settings.COGNITO_REDIRECT_URI,
        "scope": "openid email profile",
        "state": state,
    }
    authorize_url = f"https://{settings.COGNITO_DOMAIN}/oauth2/authorize?{urlencode(params)}"
    return redirect(authorize_url)


def callback(request):
    # 1. Cognito may send an error (e.g. user cancelled)
    if "error" in request.GET:
        return HttpResponseBadRequest(f"Login failed: {request.GET.get('error_description', request.GET['error'])}")

    code = request.GET.get("code")
    state = request.GET.get("state")

    # 2. Check state matches the one we saved in /login/
    if not code or state != request.session.pop("oauth_state", None):
        return HttpResponseBadRequest("Invalid login response (state mismatch). Please try logging in again.")

    # 3. Exchange the code for tokens. This call goes from our server to Cognito,
    #    and uses the client secret, which the browser never sees.
    token_url = f"https://{settings.COGNITO_DOMAIN}/oauth2/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": settings.COGNITO_CLIENT_ID,
        "code": code,
        "redirect_uri": settings.COGNITO_REDIRECT_URI,
    }
    auth = (settings.COGNITO_CLIENT_ID, settings.COGNITO_CLIENT_SECRET) if settings.COGNITO_CLIENT_SECRET else None
    response = requests.post(token_url, data=data, auth=auth, timeout=10)

    if response.status_code != 200:
        return HttpResponseBadRequest(f"Could not get tokens from Cognito: {response.text}")

    tokens = response.json()  # contains id_token, access_token, refresh_token

    # 4. Save the tokens in the Django session (stored server side, browser only gets a session cookie)
    request.session["id_token"] = tokens["id_token"]
    request.session["access_token"] = tokens["access_token"]
    return redirect("welcome")
