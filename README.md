# Cognito Login in a Django App

**Subject:** iMAD (Introduction to Mobile App Development), Group Project
**Topic 1:** A Django app where users log in and log out through an AWS Cognito User Pool (Hosted UI) and land on a welcome page.

---

## Team Members & Roles

| Member | Role | What they built |
|---|---|---|
| **Rhythem Kalra** | Repo owner & AWS setup | GitHub repo, Django project skeleton, settings + `.env` handling, `.gitignore`, base layout + home page, Cognito User Pool + App Client + Hosted UI setup |
| **Bhoomi** | Login flow | `/login/` (redirect to Hosted UI with `state`) and `/callback/` (state check + code-for-token exchange) in `accounts/views_login.py` |
| **Krati** | Token verification & Welcome page | `accounts/jwt_utils.py` (verifies JWT signature via JWKS, expiry, issuer, audience), `/welcome/` view and `welcome.html`, plus the **JWT tamper test** page (`views_tamper.py`) |
| **Kanishka** | Logout & Documentation | `/logout/` (clears session + Cognito logout) in `accounts/views_logout.py`, README, architecture diagram, flowchart, screenshots |

---

## What the app does

1. **Home page** (`/`) shows a **Login with Cognito** button.
2. **Login** (`/login/`) sends the user to the **Cognito Hosted UI**, a login page hosted by AWS. Our app never sees the password.
3. After login, Cognito redirects back to **`/callback/`** with a one-time **code**. Django exchanges that code for **tokens** (JWTs).
4. **Welcome page** (`/welcome/`) verifies the ID token and shows the user's name, email and the token's contents.
5. **Tamper test** (`/tamper-test/`) breaks the real token in four ways and shows that every fake version is rejected.
6. **Logout** (`/logout/`) clears the Django session and logs the user out of Cognito too.

---

## Architecture

![Architecture diagram](docs/architecture.png)

```mermaid
sequenceDiagram
    participant B as Browser
    participant D as Django App
    participant C as AWS Cognito
    B->>D: GET /login/
    D->>B: Redirect to Cognito /oauth2/authorize (+ state)
    B->>C: User signs in on Hosted UI
    C->>B: Redirect to /callback/?code=...&state=...
    B->>D: GET /callback/?code=...
    D->>C: POST /oauth2/token (code + client secret)
    C->>D: id_token, access_token, refresh_token
    D->>D: Save tokens in session, verify ID token (JWKS)
    D->>B: Welcome page
    B->>D: GET /logout/
    D->>B: Clear session, redirect to Cognito /logout
    C->>B: Redirect back to Home
```

### Flowchart

![Flowchart](docs/flowchart.png)

### Project structure

```
cognito-django-login/
├── config/              # Django project settings & root URLs
│   ├── settings.py      # reads Cognito values from .env
│   └── urls.py
├── accounts/            # our app
│   ├── urls.py          # /, /login/, /callback/, /welcome/, /logout/
│   ├── views_home.py    # Home page             (Rhythem)
│   ├── views_login.py   # Login + callback      (Bhoomi)
│   ├── jwt_utils.py     # JWT verification      (Krati)
│   ├── views_welcome.py # Welcome page          (Krati)
│   ├── views_tamper.py  # JWT tamper test       (Krati)
│   └── views_logout.py  # Logout                (Kanishka)
├── templates/           # base.html, home.html, welcome.html
├── docs/                # diagrams + screenshots
├── .env.example         # template for secrets (real .env is NOT committed)
├── .gitignore
└── requirements.txt
```

---

## Setup Steps

### 1. AWS Cognito (done once by one person, free tier)

1. Log in to the **AWS Console** and set the region (top right) to **Asia Pacific (Mumbai) ap-south-1**.
2. Search **Cognito** → **Create user pool**.
3. Application type: **Traditional web application**. Name it `django-cognito-app`.
4. Sign-in identifiers: **Email**. Required attributes for sign-up: **email** (optionally **name**).
5. **Return URL:** `http://localhost:8000/callback/` → **Create**.
6. Open the new pool → **App clients** → your app client → **Login pages** → **Edit**:
   - Allowed callback URLs: `http://localhost:8000/callback/`
   - Allowed sign-out URLs: `http://localhost:8000/`
   - OAuth grant type: **Authorization code grant**
   - Scopes: **openid**, **email**, **profile** → **Save**.
7. Note down these values:
   - **User pool ID** (pool overview page, e.g. `ap-south-1_AbC123`)
   - **Client ID** and **Client secret** (App client page)
   - **Domain** (left menu → **Domain**, e.g. `ap-south-1abc123.auth.ap-south-1.amazoncognito.com`)

### 2. Run the app locally

```bash
git clone https://github.com/<owner>/cognito-django-login.git
cd cognito-django-login
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # Windows: copy .env.example .env
# open .env and paste the Cognito values from step 1
python manage.py migrate          # creates the session table
python manage.py runserver
```

Open **http://localhost:8000** (use `localhost`, not `127.0.0.1`, because it must match the callback URL).

---

## Screenshots

| Home | Cognito Hosted UI |
|---|---|
| ![Home](docs/screenshots/1-home.png) | ![Hosted UI](docs/screenshots/2-hosted-ui.png) |

| Welcome (after login) | After logout |
|---|---|
| ![Welcome](docs/screenshots/3-welcome.png) | ![Logged out](docs/screenshots/4-logged-out.png) |

---

## Research Questions (in our own words)

### Q1. What are a user pool and an app client? (Rhythem)

A **user pool** is a user directory that AWS Cognito manages for us. It stores every user who signs up (email, password, verified status, attributes like name) and handles sign-up, sign-in, password reset and email verification. Because of this, our Django app does not need its own users table or password storage.

An **app client** is how a specific application gets permission to use the user pool. One user pool can have many app clients, for example a web app and a mobile app. Each app client has its own **Client ID** (and optionally a **Client Secret**), its allowed callback and sign-out URLs, the OAuth flows it may use, and the scopes it may request. Our Django app is one app client. When it sends a user to the Hosted UI, Cognito checks the client ID and only redirects back to the URLs we whitelisted.

### Q2. What is a JWT and what does it contain? (Krati)

A **JWT (JSON Web Token)** is like a sealed ID card that Cognito hands the user after login. It is one long string in three parts separated by dots: `header.payload.signature`.

- **Header:** how the token was sealed (`RS256`) and which key was used (`kid`).
- **Payload:** the actual information, called claims. Ours has `sub` (the user's unique ID), `email`, `name`, `iss` (which user pool issued it), `aud` (which app it was made for), `token_use`, `iat` (when it was issued) and `exp` (when it expires).
- **Signature:** the seal. Cognito creates it with a private key that only Cognito has, and we check it using Cognito's public key from its JWKS address.

The payload is not secret. Anyone can decode it and read it. What makes a JWT trustworthy is the signature. In our tamper test, changing the email to `hacker@evil.com` made the signature stop matching, so the token was rejected straight away.

Cognito gives three tokens: the **ID token** (who the user is), the **access token** (what the user may access) and the **refresh token** (to get new tokens later without logging in again).

### Q3. How does the OAuth 2.0 redirect login flow work, step by step? (Bhoomi)

We use the **Authorization Code grant**:

1. The user clicks **Login** on our app.
2. Our app redirects the browser to Cognito's `/oauth2/authorize` URL with:
   - `client_id`
   - `redirect_uri`
   - `response_type=code`
   - `scope=openid email profile`
   - a random `state` value, which we also save in the session
3. Cognito shows its **Hosted UI**. The user signs up or signs in there, so the password goes only to Cognito.
4. Cognito redirects the browser back to our `redirect_uri` (`/callback/`) with a short-lived, one-time **authorization code** and the same `state`.
5. Our app checks that `state` matches what it saved. This protects against CSRF and fake callbacks.
6. Our server sends the code, along with the client ID and **client secret**, directly to Cognito's `/oauth2/token` endpoint. This is server-to-server, so the browser never sees the secret or the tokens.
7. Cognito returns the **ID token, access token and refresh token**.
8. Our app verifies the ID token, stores the tokens in the session, and shows the Welcome page.
9. On **logout**, we clear our session and redirect to Cognito's `/logout` endpoint so Cognito's own session ends too. Cognito then redirects back to our home page.

The code is exchanged instead of sending tokens directly in the URL because URLs can leak through browser history and logs. A code is useless without the client secret, which only our server has.

---

## JWT Tamper Test

From the Welcome page, click **Run tamper test**. The app takes the real ID token and runs five versions through the same verification:

| Test | What we changed | Result |
|---|---|---|
| Original token | nothing | ✅ Accepted |
| Payload edited | email changed to `hacker@evil.com`, old signature kept | ❌ `InvalidSignatureError` |
| Signature edited | one letter of the signature changed | ❌ `InvalidSignatureError` |
| Expired token | checked as if its expiry time had passed | ❌ `ExpiredSignatureError` |
| Token for another app | checked against a different client ID | ❌ `InvalidAudienceError` |

This proves that reading a JWT is not enough: anyone can edit the payload, but without Cognito's private key they cannot make a matching signature.

![Tamper test](docs/screenshots/5-tamper-test.png)

---

## Security notes

- Secrets live in `.env`, which is listed in `.gitignore` and never committed. `.env.example` shows the format only.
- The `state` parameter prevents CSRF on the callback.
- Tokens are stored in the server-side session, not in browser localStorage.
- The ID token is verified with Cognito's public keys, which are **cached** so we don't call AWS on every request.
- Only AWS free tier is used (Cognito Lite tier is free for up to 10,000 monthly active users).
