"""
Tamper test page (Krati).

Takes the real ID token from the session and runs it through the same
verification as the welcome page, plus 4 broken versions:
  1. Payload changed (email edited)  -> signature no longer matches
  2. Signature changed (1 letter)    -> signature invalid
  3. Token treated as expired        -> expiry check fails
  4. Token checked for another app   -> audience check fails
This shows WHY we verify the JWT instead of just reading it.
"""
import base64
import json

import jwt
from django.shortcuts import redirect, render

from .jwt_utils import verify_id_token


def _b64url_decode(part):
    return base64.urlsafe_b64decode(part + "=" * (-len(part) % 4))


def _b64url_encode(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _run(label, explanation, token, **kwargs):
    try:
        verify_id_token(token, **kwargs)
        return {"label": label, "explanation": explanation, "ok": True, "result": "Accepted: token is valid"}
    except jwt.PyJWTError as e:
        return {"label": label, "explanation": explanation, "ok": False,
                "result": f"Rejected: {type(e).__name__} ({e})"}


def tamper_test(request):
    token = request.session.get("id_token")
    if not token:
        return redirect("home")

    header, payload, signature = token.split(".")

    # 1. Edit the payload: pretend to be someone else, keep Cognito's old signature
    claims = json.loads(_b64url_decode(payload))
    claims["email"] = "hacker@evil.com"
    fake_payload = _b64url_encode(json.dumps(claims, separators=(",", ":")).encode())
    edited_payload_token = f"{header}.{fake_payload}.{signature}"

    # 2. Change ONE character of the signature
    flipped = ("A" if signature[10] != "A" else "B")
    edited_signature_token = f"{header}.{payload}.{signature[:10]}{flipped}{signature[11:]}"

    tests = [
        _run("Original token from Cognito", "The real token we received at login.", token),
        _run("Payload edited", "Email changed to hacker@evil.com but the old signature kept.", edited_payload_token),
        _run("Signature edited", "Only one letter of the signature changed.", edited_signature_token),
        # negative leeway makes the library treat the token as already past its 'exp' time
        _run("Expired token", "Same token, checked as if its expiry time had passed.", token, leeway=-100000,
             options={"verify_iat": False}),
        _run("Token for another app", "Same token, checked as if our app had a different client ID.",
             token, audience="some-other-app-client-id"),
    ]
    return render(request, "tamper.html", {"tests": tests})
