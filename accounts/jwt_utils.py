"""
JWT verification (Krati).

The ID token is a JWT signed by Cognito. Before trusting what is inside it,
we check the signature using Cognito's public keys (JWKS), plus expiry,
issuer and audience.
"""
import jwt
from django.conf import settings

_jwk_client = None


def _get_jwk_client():
    # PyJWKClient downloads Cognito's public keys once and caches them,
    # so we don't call AWS on every page load.
    global _jwk_client
    if _jwk_client is None:
        jwks_url = f"{issuer()}/.well-known/jwks.json"
        _jwk_client = jwt.PyJWKClient(jwks_url, cache_keys=True)
    return _jwk_client


def issuer():
    return f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}"


def verify_id_token(token, audience=None, leeway=0, options=None):
    """Returns the token's claims (a dict) if valid, raises jwt.PyJWTError if not.

    audience and leeway are only changed by the tamper-test page, to simulate
    a token meant for another app or a token that has expired.
    """
    signing_key = _get_jwk_client().get_signing_key_from_jwt(token)
    claims = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        audience=audience or settings.COGNITO_CLIENT_ID,  # token was made for OUR app client
        issuer=issuer(),                                    # token was made by OUR user pool
        leeway=leeway,
        options=options,
    )                                           # expiry ('exp') is checked automatically
    if claims.get("token_use") != "id":
        raise jwt.InvalidTokenError("Not an ID token")
    return claims
