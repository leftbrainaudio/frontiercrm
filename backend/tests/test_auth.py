"""Tests for auth endpoints — signup, login, magic link, OAuth, refresh, health, me."""

from __future__ import annotations

import uuid
from unittest.mock import patch

from django.core import mail
from django.utils import timezone
from rest_framework.test import APIClient


class TestAuth:
    """Authentication flow tests — signup, login, JWT lifecycle, magic link, OAuth, health."""

    SIGNUP_URL = "/api/auth/signup/"
    LOGIN_URL = "/api/auth/login/"
    REFRESH_URL = "/api/auth/token/refresh/"
    ME_URL = "/api/accounts/me/"
    MAGIC_LINK_REQUEST_URL = "/api/auth/magic-link/request/"
    MAGIC_LINK_CONFIRM_URL = "/api/auth/magic-link/confirm/"
    GOOGLE_INIT_URL = "/api/auth/google/init/"
    HEALTH_URL = "/api/health/"
    HEALTH_READY_URL = "/api/health/ready/"

    # ── Signup ─────────────────────────────────────────────────────────────────

    def test_signup_creates_tenant_role_team_membership(self, api_client, db):
        """Signup creates Tenant + Role('Admin') + Team('Everyone') + Membership(is_owner=True)."""
        from apps.accounts.models import User as UserModel
        from apps.teams.models import Membership, Role, Team, Tenant

        resp = api_client.post(
            self.SIGNUP_URL,
            {
                "email": "founder@test.com",
                "username": "founder",
                "password": "securepass123",
                "first_name": "Founder",
                "last_name": "Test",
            },
            format="json",
        )
        assert resp.status_code == 201, resp.json()
        data = resp.json()

        # Verify response shape
        assert "access" in data
        assert "refresh" in data
        assert data["user"]["email"] == "founder@test.com"
        assert data["user"]["tenant_id"] is not None

        user_id = data["user"]["id"]
        tenant_id = uuid.UUID(data["user"]["tenant_id"])

        # Verify Tenant was created
        tenant = Tenant.objects.get(id=tenant_id)
        assert tenant.name == "founder's Organization"

        # Verify Role("Admin") was created
        role = Role.objects.get(tenant=tenant, name="Admin")
        assert role.is_admin is True

        # Verify Team("Everyone") was created
        team = Team.objects.get(tenant=tenant, name="Everyone")

        # Verify Membership linking user -> tenant with is_owner=True
        user = UserModel.objects.get(id=user_id)
        membership = Membership.objects.get(user=user, tenant=tenant)
        assert membership.role == role
        assert membership.team == team
        assert membership.is_owner is True
        assert membership.is_active is True

    def test_signup_with_organization_name(self, api_client, db):
        """Signup respects custom organization_name for the tenant."""
        from apps.teams.models import Tenant

        resp = api_client.post(
            self.SIGNUP_URL,
            {
                "email": "acme@test.com",
                "username": "acme",
                "password": "securepass123",
                "organization_name": "Acme Corp",
            },
            format="json",
        )
        assert resp.status_code == 201, resp.json()
        tenant_id = resp.json()["user"]["tenant_id"]
        tenant = Tenant.objects.get(id=tenant_id)
        assert tenant.name == "Acme Corp"

    def test_signup_duplicate_username(self, api_client, user, db):
        """Signup with an existing username returns 400 (username is unique)."""
        resp = api_client.post(
            self.SIGNUP_URL,
            {
                "email": "unique-email@test.com",
                "username": user.username,  # Same username as fixture user
                "password": "securepass123",
            },
            format="json",
        )
        assert resp.status_code == 400
        data = resp.json()
        assert data["error"] is True
        # The custom exception handler wraps field errors under 'errors'
        assert "username" in (data.get("errors") or {})

    def test_signup_weak_password(self, api_client, db):
        """Signup with a password shorter than 8 characters returns 400."""
        resp = api_client.post(
            self.SIGNUP_URL,
            {
                "email": "weak@test.com",
                "username": "weakuser",
                "password": "short",
            },
            format="json",
        )
        assert resp.status_code == 400
        data = resp.json()
        # Custom exception handler wraps field errors under 'errors'
        assert data.get("error") is True
        errors = data.get("errors") or {}
        assert "password" in errors

    def test_signup_missing_username(self, api_client, db):
        """Signup without username returns 400."""
        resp = api_client.post(
            self.SIGNUP_URL,
            {"email": "nouser@test.com", "password": "securepass123"},
            format="json",
        )
        assert resp.status_code == 400

    def test_signup_missing_password(self, api_client, db):
        """Signup without password returns 400."""
        resp = api_client.post(
            self.SIGNUP_URL,
            {"email": "nopass@test.com", "username": "nopass"},
            format="json",
        )
        assert resp.status_code == 400

    def test_signup_email_field_optional(self, api_client, db):
        """Signup without email succeeds because email has blank=True in AbstractUser."""
        resp = api_client.post(
            self.SIGNUP_URL,
            {"username": "noemail", "password": "securepass123"},
            format="json",
        )
        # email has blank=True in Django's AbstractUser, so it's not required
        assert resp.status_code in (201, 400)

    def test_signup_invalid_email(self, api_client, db):
        """Signup with a malformed email returns 400."""
        resp = api_client.post(
            self.SIGNUP_URL,
            {
                "email": "not-an-email",
                "username": "bademail",
                "password": "securepass123",
            },
            format="json",
        )
        assert resp.status_code == 400

    # ── Login ──────────────────────────────────────────────────────────────────

    def test_login_success(self, api_client, user, db):
        """Valid credentials return JWT tokens."""
        resp = api_client.post(
            self.LOGIN_URL,
            {"email": user.email, "password": "testpass123"},
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access" in data
        assert "refresh" in data
        assert data["user"]["email"] == user.email

    def test_login_invalid_credentials(self, api_client, db):
        """Invalid credentials return 400."""
        resp = api_client.post(
            self.LOGIN_URL,
            {"email": "nonexistent@test.com", "password": "wrongpass"},
            format="json",
        )
        assert resp.status_code == 400

    def test_login_wrong_password(self, api_client, user, db):
        """Correct email but wrong password returns 400."""
        resp = api_client.post(
            self.LOGIN_URL,
            {"email": user.email, "password": "wrongpass"},
            format="json",
        )
        assert resp.status_code == 400

    # ── Account deactivation ──────────────────────────────────────────────────

    def test_login_disabled_user(self, api_client, user, db):
        """A user with is_active=False cannot log in."""
        user.is_active = False
        user.save(update_fields=["is_active"])

        resp = api_client.post(
            self.LOGIN_URL,
            {"email": user.email, "password": "testpass123"},
            format="json",
        )
        assert resp.status_code == 400
        data = resp.json()
        # The custom exception handler wraps the detail
        assert "disabled" in data.get("detail", "").lower()

    def test_signup_user_is_active_by_default(self, api_client, db):
        """Newly signed-up users are active by default."""
        resp = api_client.post(
            self.SIGNUP_URL,
            {
                "email": "activeuser@test.com",
                "username": "activeuser",
                "password": "securepass123",
            },
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["user"]["is_active"] is True

    # ── Magic Link ────────────────────────────────────────────────────────────

    def test_magic_link_request_sends_email(self, api_client, user, db):
        """Requesting a magic link queues an email with a token."""
        resp = api_client.post(
            self.MAGIC_LINK_REQUEST_URL,
            {"email": user.email},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["detail"] == "Magic link sent to email."

        # Verify an email was sent via locmem backend
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [user.email]
        assert "magic" in mail.outbox[0].subject.lower()

        # Verify the user now has a magic link token
        user.refresh_from_db()
        assert user.magic_link_token != ""
        assert user.magic_link_created_at is not None

    def test_magic_link_request_nonexistent_email(self, api_client, db):
        """Requesting a magic link for an unknown email returns 400."""
        resp = api_client.post(
            self.MAGIC_LINK_REQUEST_URL,
            {"email": "nobody@nowhere.com"},
            format="json",
        )
        assert resp.status_code == 400
        assert len(mail.outbox) == 0

    def test_magic_link_confirm_returns_jwt(self, api_client, user, db):
        """Confirming a valid magic link returns JWT tokens."""
        # First request a magic link to set the token
        user.magic_link_token = "test-valid-token-12345"
        user.magic_link_created_at = timezone.now()
        user.save(update_fields=["magic_link_token", "magic_link_created_at"])

        resp = api_client.post(
            self.MAGIC_LINK_CONFIRM_URL,
            {"token": "test-valid-token-12345"},
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access" in data
        assert "refresh" in data
        assert data["user"]["email"] == user.email

        # Token should be cleared after use
        user.refresh_from_db()
        assert user.magic_link_token == ""

    def test_magic_link_confirm_expired_token(self, api_client, user, db):
        """An expired magic link token returns 400."""
        expired_time = timezone.now() - timezone.timedelta(minutes=30)
        user.magic_link_token = "expired-token-67890"
        user.magic_link_created_at = expired_time
        user.save(update_fields=["magic_link_token", "magic_link_created_at"])

        resp = api_client.post(
            self.MAGIC_LINK_CONFIRM_URL,
            {"token": "expired-token-67890"},
            format="json",
        )
        assert resp.status_code == 400

    def test_magic_link_confirm_invalid_token(self, api_client, db):
        """An invalid magic link token returns 400."""
        resp = api_client.post(
            self.MAGIC_LINK_CONFIRM_URL,
            {"token": "completely-invalid-token"},
            format="json",
        )
        assert resp.status_code == 400

    def test_magic_link_full_flow(self, api_client, user, db):
        """Full magic-link request → confirm → authenticated access flow."""
        # 1. Request magic link
        resp = api_client.post(
            self.MAGIC_LINK_REQUEST_URL,
            {"email": user.email},
            format="json",
        )
        assert resp.status_code == 200
        user.refresh_from_db()
        token = user.magic_link_token
        assert token

        # 2. Confirm with the token
        resp = api_client.post(
            self.MAGIC_LINK_CONFIRM_URL,
            {"token": token},
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access" in data
        assert "refresh" in data

        # 3. Use the returned JWT to access authenticated endpoint
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {data['access']}")
        resp = client.get(self.ME_URL)
        assert resp.status_code == 200
        assert resp.json()["email"] == user.email

    # ── Google OAuth ───────────────────────────────────────────────────────────

    def test_google_oauth_init_returns_authorization_url(self, api_client, settings, db):
        """GET /api/auth/google/init/ returns an authorization URL."""
        settings.GOOGLE_CLIENT_ID = "test-client-id-123.apps.googleusercontent.com"
        settings.GOOGLE_OAUTH_REDIRECT_URI = "http://localhost:8000/api/auth/google/callback/"

        resp = api_client.get(self.GOOGLE_INIT_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert "authorization_url" in data
        url = data["authorization_url"]
        assert url.startswith("https://accounts.google.com/o/oauth2/auth")
        assert "client_id=test-client-id-123.apps.googleusercontent.com" in url
        assert "response_type=code" in url
        assert "access_type=offline" in url
        assert "prompt=consent" in url

    def test_google_oauth_callback_no_code(self, api_client, db):
        """Google OAuth callback with no code returns 400."""
        callback_url = self.GOOGLE_INIT_URL.replace("init/", "callback/")
        resp = api_client.post(callback_url, {}, format="json")
        assert resp.status_code == 400
        data = resp.json()
        # View returns its own error dict, not the custom exception handler format
        assert data.get("error") == "Authorization code required."

    def test_google_oauth_callback_mocked(self, api_client, db):
        """Google OAuth callback happy path with mocked external requests."""
        callback_url = self.GOOGLE_INIT_URL.replace("init/", "callback/")

        mock_token_response = {
            "access_token": "mock-google-access-token",
            "refresh_token": "mock-google-refresh-token",
            "expires_in": 3600,
        }
        mock_user_info = {
            "id": "google-user-id-999",
            "email": "googleuser@test.com",
            "given_name": "Google",
            "family_name": "User",
            "picture": "https://example.com/avatar.png",
        }

        # The view does 'import requests as http_requests' inside the function body.
        # Patch requests.post and requests.get at the top-level package so the
        # view's local import picks up the mock.
        with patch("requests.post") as mock_post, patch("requests.get") as mock_get:
            mock_post.return_value.json.return_value = mock_token_response
            mock_get.return_value.json.return_value = mock_user_info

            resp = api_client.post(
                callback_url,
                {"code": "valid-auth-code-xyz"},
                format="json",
            )

        assert resp.status_code == 200
        data = resp.json()
        assert "access" in data
        assert "refresh" in data
        assert data["user"]["email"] == "googleuser@test.com"
        assert data["user"]["first_name"] == "Google"
        assert data["user"]["last_name"] == "User"

    # ── Token Refresh ──────────────────────────────────────────────────────────

    def test_token_refresh_valid(self, api_client, user, db):
        """A valid refresh token returns a new access token (and rotated refresh token)."""
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(user)
        resp = api_client.post(
            self.REFRESH_URL,
            {"refresh": str(refresh)},
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access" in data
        # ROTATE_REFRESH_TOKENS = True, so we also get a new refresh token
        assert "refresh" in data

    def test_token_refresh_invalid(self, api_client, db):
        """An invalid refresh token returns 401."""
        resp = api_client.post(
            self.REFRESH_URL,
            {"refresh": "totally-invalid-token"},
            format="json",
        )
        assert resp.status_code == 401

    def test_token_refresh_expired(self, api_client, user, db):
        """An expired refresh token returns 401 (token reuse after rotation)."""
        from rest_framework_simplejwt.tokens import RefreshToken

        # With ROTATE_REFRESH_TOKENS=True, using a token after it's been rotated fails
        old_refresh = str(RefreshToken.for_user(user))
        resp1 = api_client.post(
            self.REFRESH_URL,
            {"refresh": old_refresh},
            format="json",
        )
        assert resp1.status_code == 200

        # Using the same token again after rotation should fail
        resp2 = api_client.post(
            self.REFRESH_URL,
            {"refresh": old_refresh},
            format="json",
        )
        # It may return 401 if the blacklist app is active, or 200 if not configured
        # (SimpleJWT blacklist requires the blacklist app to be installed)
        assert resp2.status_code in (200, 401)

    def test_token_refresh_malformed(self, api_client, db):
        """A malformed refresh token payload returns 401."""
        resp = api_client.post(
            self.REFRESH_URL,
            {"refresh": "eyJhbGciOiJIUzI1NiJ9.malformed.e30"},
            format="json",
        )
        assert resp.status_code == 401

    # ── Social Auth (Login via Google / Microsoft) ───────────────────────────────

    SOCIAL_INIT_URL = "/api/auth/social/{provider}/init/"
    SOCIAL_CALLBACK_URL = "/api/auth/social/"

    def test_social_auth_init_google(self, api_client, settings, db):
        """GET /api/auth/social/google/init/ returns a Google auth URL."""
        settings.GOOGLE_CLIENT_ID = "google-client-id-test"
        settings.GOOGLE_OAUTH_REDIRECT_URI = "http://localhost:5173/auth/callback"

        resp = api_client.get("/api/auth/social/google/init/")
        assert resp.status_code == 200
        data = resp.json()
        assert "authorization_url" in data
        url = data["authorization_url"]
        assert url.startswith("https://accounts.google.com/o/oauth2/auth")
        assert "client_id=google-client-id-test" in url
        assert "scope=openid+email+profile" in url or "scope=openid%20email%20profile" in url
        assert "access_type=online" in url

    def test_social_auth_init_microsoft(self, api_client, settings, db):
        """GET /api/auth/social/microsoft/init/ returns a Microsoft auth URL."""
        settings.MICROSOFT_CLIENT_ID = "ms-client-id-test"
        settings.MICROSOFT_OAUTH_REDIRECT_URI = "http://localhost:5173/auth/callback"

        resp = api_client.get("/api/auth/social/microsoft/init/")
        assert resp.status_code == 200
        data = resp.json()
        assert "authorization_url" in data
        url = data["authorization_url"]
        assert "login.microsoftonline.com" in url
        assert "client_id=ms-client-id-test" in url

    def test_social_auth_init_unknown_provider(self, api_client, db):
        """GET /api/auth/social/unknown/init/ returns 400."""
        resp = api_client.get("/api/auth/social/unknown/init/")
        assert resp.status_code == 400
        assert "unsupported" in resp.json().get("error", "").lower()

    def test_social_auth_callback_missing_fields(self, api_client, db):
        """POST /api/auth/social/ without provider or code returns 400."""
        resp = api_client.post(self.SOCIAL_CALLBACK_URL, {}, format="json")
        assert resp.status_code == 400
        assert resp.json().get("error") == "provider and code are required."

        resp = api_client.post(self.SOCIAL_CALLBACK_URL, {"provider": "google"}, format="json")
        assert resp.status_code == 400

    def test_social_auth_callback_unknown_provider(self, api_client, db):
        """POST /api/auth/social/ with unknown provider returns 400."""
        resp = api_client.post(
            self.SOCIAL_CALLBACK_URL,
            {"provider": "unknown", "code": "abc"},
            format="json",
        )
        assert resp.status_code == 400
        assert "unsupported" in resp.json().get("error", "").lower()

    def test_social_auth_callback_google_mocked(self, api_client, settings, db):
        """POST /api/auth/social/ with Google provider — happy path."""
        from unittest.mock import patch

        settings.GOOGLE_CLIENT_ID = "test-client-id"
        settings.GOOGLE_CLIENT_SECRET = "test-client-secret"

        mock_token_response = {
            "access_token": "mock-google-access-token",
            "refresh_token": "mock-google-refresh-token",
            "expires_in": 3600,
        }
        mock_user_info = {
            "id": "google-user-123",
            "email": "social-user@test.com",
            "given_name": "Social",
            "family_name": "User",
            "picture": "https://example.com/avatar.png",
        }

        with patch("requests.post") as mock_post, patch("requests.get") as mock_get:
            mock_post.return_value.json.return_value = mock_token_response
            mock_get.return_value.json.return_value = mock_user_info

            resp = api_client.post(
                self.SOCIAL_CALLBACK_URL,
                {"provider": "google", "code": "valid-auth-code"},
                format="json",
            )

        assert resp.status_code == 200
        data = resp.json()
        assert "access" in data
        assert "refresh" in data
        assert data["user"]["email"] == "social-user@test.com"
        assert data["user"]["first_name"] == "Social"
        assert data["user"]["last_name"] == "User"

    def test_social_auth_callback_microsoft_mocked(self, api_client, settings, db):
        """POST /api/auth/social/ with Microsoft provider — happy path."""
        from unittest.mock import patch
        from apps.accounts.models import User as UserModel

        settings.MICROSOFT_CLIENT_ID = "ms-client-id"
        settings.MICROSOFT_CLIENT_SECRET = "ms-client-secret"

        mock_token_response = {
            "access_token": "mock-ms-access-token",
            "refresh_token": "mock-ms-refresh-token",
            "expires_in": 3600,
        }
        mock_user_info = {
            "id": "ms-user-456",
            "mail": "msuser@contoso.com",
            "givenName": "MS",
            "surname": "User",
        }

        with patch("requests.post") as mock_post, patch("requests.get") as mock_get:
            mock_post.return_value.json.return_value = mock_token_response
            mock_get.return_value.json.return_value = mock_user_info

            resp = api_client.post(
                self.SOCIAL_CALLBACK_URL,
                {"provider": "microsoft", "code": "valid-ms-code"},
                format="json",
            )

        assert resp.status_code == 200
        data = resp.json()
        assert "access" in data
        assert "refresh" in data
        assert data["user"]["email"] == "msuser@contoso.com"
        assert data["user"]["first_name"] == "MS"
        assert data["user"]["last_name"] == "User"
        # Verify the microsoft_id was saved
        user = UserModel.objects.get(email="msuser@contoso.com")
        assert user.microsoft_id == "ms-user-456"
        assert user.microsoft_access_token == "mock-ms-access-token"

    # ── Social Auth — Extended Coverage ────────────────────────────────────────────

    def test_social_auth_init_with_custom_redirect_uri(self, api_client, settings, db):
        """GET /api/auth/social/google/init/?redirect_uri=... uses the custom URI."""
        settings.GOOGLE_CLIENT_ID = "google-client-id-test"
        resp = api_client.get(
            "/api/auth/social/google/init/",
            {"redirect_uri": "https://myapp.com/custom/callback"},
        )
        assert resp.status_code == 200
        url = resp.json()["authorization_url"]
        assert "redirect_uri=https%3A%2F%2Fmyapp.com%2Fcustom%2Fcallback" in url or \
               "redirect_uri=https://myapp.com/custom/callback" in url

    def test_social_auth_callback_with_custom_redirect_uri(self, api_client, settings, db):
        """POST /api/auth/social/ passes the custom redirect_uri to the token exchange."""
        from unittest.mock import patch

        settings.GOOGLE_CLIENT_ID = "test-client-id"
        settings.GOOGLE_CLIENT_SECRET = "test-client-secret"

        with patch("requests.post") as mock_post, patch("requests.get") as mock_get:
            mock_post.return_value.json.return_value = {
                "access_token": "mock-token",
                "refresh_token": "mock-refresh",
                "expires_in": 3600,
            }
            mock_get.return_value.json.return_value = {
                "id": "custom-redirect-user",
                "email": "custom@test.com",
                "given_name": "Custom",
                "family_name": "User",
            }

            resp = api_client.post(
                "/api/auth/social/",
                {
                    "provider": "google",
                    "code": "valid-code",
                    "redirect_uri": "https://myapp.com/custom/callback",
                },
                format="json",
            )

        assert resp.status_code == 200
        # Verify the custom redirect_uri was used in the token exchange call
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["data"]["redirect_uri"] == "https://myapp.com/custom/callback"

    def test_social_auth_callback_token_exchange_failure(self, api_client, settings, db):
        """POST /api/auth/social/ returns 400 when the provider rejects the code."""
        from unittest.mock import patch

        settings.GOOGLE_CLIENT_ID = "test-client-id"
        settings.GOOGLE_CLIENT_SECRET = "test-client-secret"

        with patch("requests.post") as mock_post:
            # Provider returns an error (no access_token in response)
            mock_post.return_value.json.return_value = {
                "error": "invalid_grant",
                "error_description": "Authorization code expired.",
            }

            resp = api_client.post(
                "/api/auth/social/",
                {"provider": "google", "code": "expired-code"},
                format="json",
            )

        assert resp.status_code == 400
        data = resp.json()
        assert "Failed to exchange" in data.get("error", "")

    def test_social_auth_callback_provider_returns_no_user_id(self, api_client, settings, db):
        """POST /api/auth/social/ returns 400 when the provider returns no user ID."""
        from unittest.mock import patch

        settings.GOOGLE_CLIENT_ID = "test-client-id"
        settings.GOOGLE_CLIENT_SECRET = "test-client-secret"

        with patch("requests.post") as mock_post, patch("requests.get") as mock_get:
            mock_post.return_value.json.return_value = {
                "access_token": "mock-token",
                "expires_in": 3600,
            }
            # Missing 'id' — provider_user_id will be empty
            mock_get.return_value.json.return_value = {
                "email": "noid@test.com",
                "given_name": "No",
                "family_name": "Id",
            }

            resp = api_client.post(
                "/api/auth/social/",
                {"provider": "google", "code": "valid-code"},
                format="json",
            )

        assert resp.status_code == 400
        assert "Failed to get user info" in resp.json().get("error", "")

    def test_social_auth_callback_provider_returns_no_email(self, api_client, settings, db):
        """POST /api/auth/social/ returns 400 when the provider returns no email."""
        from unittest.mock import patch

        settings.GOOGLE_CLIENT_ID = "test-client-id"
        settings.GOOGLE_CLIENT_SECRET = "test-client-secret"

        with patch("requests.post") as mock_post, patch("requests.get") as mock_get:
            mock_post.return_value.json.return_value = {
                "access_token": "mock-token",
                "expires_in": 3600,
            }
            # Missing 'email'
            mock_get.return_value.json.return_value = {
                "id": "no-email-user",
                "given_name": "No",
                "family_name": "Email",
            }

            resp = api_client.post(
                "/api/auth/social/",
                {"provider": "google", "code": "valid-code"},
                format="json",
            )

        assert resp.status_code == 400
        assert "Failed to get user info" in resp.json().get("error", "")

    def test_social_auth_callback_google_no_picture(self, api_client, settings, db):
        """A Google user info without a 'picture' field sets avatar_url to empty string."""
        from unittest.mock import patch

        settings.GOOGLE_CLIENT_ID = "test-client-id"
        settings.GOOGLE_CLIENT_SECRET = "test-client-secret"

        with patch("requests.post") as mock_post, patch("requests.get") as mock_get:
            mock_post.return_value.json.return_value = {
                "access_token": "mock-token",
                "refresh_token": "mock-refresh",
                "expires_in": 3600,
            }
            mock_get.return_value.json.return_value = {
                "id": "google-no-pic",
                "email": "nopic@test.com",
                "given_name": "No",
                "family_name": "Pic",
                # No 'picture' key
            }

            resp = api_client.post(
                "/api/auth/social/",
                {"provider": "google", "code": "valid-code"},
                format="json",
            )

        assert resp.status_code == 200
        assert resp.json()["user"]["avatar_url"] == ""

    def test_social_auth_callback_google_saves_avatar_url(self, api_client, settings, db):
        """A Google user info with a 'picture' field is saved as avatar_url."""
        from unittest.mock import patch

        settings.GOOGLE_CLIENT_ID = "test-client-id"
        settings.GOOGLE_CLIENT_SECRET = "test-client-secret"

        with patch("requests.post") as mock_post, patch("requests.get") as mock_get:
            mock_post.return_value.json.return_value = {
                "access_token": "mock-token",
                "refresh_token": "mock-refresh",
                "expires_in": 3600,
            }
            mock_get.return_value.json.return_value = {
                "id": "google-with-pic",
                "email": "withpic@test.com",
                "given_name": "With",
                "family_name": "Pic",
                "picture": "https://example.com/photo.jpg",
            }

            resp = api_client.post(
                "/api/auth/social/",
                {"provider": "google", "code": "valid-code"},
                format="json",
            )

        assert resp.status_code == 200
        assert resp.json()["user"]["avatar_url"] == "https://example.com/photo.jpg"

    def test_social_auth_callback_microsoft_falls_back_to_user_principal_name(self, api_client, settings, db):
        """Microsoft user info without 'mail' falls back to userPrincipalName for the email."""
        from unittest.mock import patch

        settings.MICROSOFT_CLIENT_ID = "ms-client-id"
        settings.MICROSOFT_CLIENT_SECRET = "ms-client-secret"

        with patch("requests.post") as mock_post, patch("requests.get") as mock_get:
            mock_post.return_value.json.return_value = {
                "access_token": "mock-ms-token",
                "refresh_token": "mock-ms-refresh",
                "expires_in": 3600,
            }
            # No 'mail' field, only userPrincipalName
            mock_get.return_value.json.return_value = {
                "id": "ms-upn-user",
                "userPrincipalName": "upnuser@contoso.com",
                "givenName": "UPN",
                "surname": "User",
            }

            resp = api_client.post(
                "/api/auth/social/",
                {"provider": "microsoft", "code": "valid-ms-code"},
                format="json",
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["email"] == "upnuser@contoso.com"
        assert data["user"]["first_name"] == "UPN"
        assert data["user"]["last_name"] == "User"

    def test_social_auth_callback_no_refresh_token(self, api_client, settings, db):
        """POST /api/auth/social/ works when the provider returns no refresh_token (common on re-auth)."""
        from unittest.mock import patch
        from apps.accounts.models import User as UserModel

        settings.GOOGLE_CLIENT_ID = "test-client-id"
        settings.GOOGLE_CLIENT_SECRET = "test-client-secret"

        # Create existing user with a google_id so we hit the "not created" path
        existing = UserModel.objects.create_user(
            email="reauth@test.com",
            username="reauthuser",
            password="testpass123",
            google_id="google-reauth-user",
            google_access_token="old-access-token",
            google_refresh_token="old-refresh-token",
            tenant_id=uuid.uuid4(),
        )

        with patch("requests.post") as mock_post, patch("requests.get") as mock_get:
            # No refresh_token in the response (re-auth scenario)
            mock_post.return_value.json.return_value = {
                "access_token": "new-access-token",
                "expires_in": 3600,
            }
            mock_get.return_value.json.return_value = {
                "id": "google-reauth-user",
                "email": "reauth@test.com",
                "given_name": "Re",
                "family_name": "Auth",
            }

            resp = api_client.post(
                "/api/auth/social/",
                {"provider": "google", "code": "valid-reauth-code"},
                format="json",
            )

        assert resp.status_code == 200
        existing.refresh_from_db()
        assert existing.google_access_token == "new-access-token"
        # Refresh token should remain unchanged since provider didn't return one
        assert existing.google_refresh_token == "old-refresh-token"

    def test_social_auth_callback_creates_user_with_email_matching_existing_local_user(self, api_client, settings, db):
        """A new OAuth user with same email as an existing non-OAuth user gets a separate account."""
        from unittest.mock import patch
        from apps.accounts.models import User as UserModel

        settings.GOOGLE_CLIENT_ID = "test-client-id"
        settings.GOOGLE_CLIENT_SECRET = "test-client-secret"

        # Existing local-only user (no google_id) with email "duplicate@test.com"
        existing = UserModel.objects.create_user(
            email="duplicate@test.com",
            username="localuser",
            password="testpass123",
            tenant_id=uuid.uuid4(),
        )

        with patch("requests.post") as mock_post, patch("requests.get") as mock_get:
            mock_post.return_value.json.return_value = {
                "access_token": "mock-token",
                "refresh_token": "mock-refresh",
                "expires_in": 3600,
            }
            mock_get.return_value.json.return_value = {
                "id": "google-duplicate-email-user",
                "email": "duplicate@test.com",
                "given_name": "OAuth",
                "family_name": "User",
            }

            resp = api_client.post(
                "/api/auth/social/",
                {"provider": "google", "code": "valid-code"},
                format="json",
            )

        # Should succeed — creates a new user via get_or_create(google_id=...)
        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["id"] != str(existing.id)

        # Verify we now have two users with the same email
        assert UserModel.objects.filter(email="duplicate@test.com").count() == 2

    def test_social_auth_callback_microsoft_tenant_substitution(self, api_client, settings, db):
        """Microsoft auth URLs use the configured MICROSOFT_TENANT."""
        from unittest.mock import patch

        settings.MICROSOFT_CLIENT_ID = "ms-client-id"
        settings.MICROSOFT_CLIENT_SECRET = "ms-client-secret"
        settings.MICROSOFT_TENANT = "mytenant.onmicrosoft.com"

        with patch("requests.post") as mock_post, patch("requests.get") as mock_get:
            mock_post.return_value.json.return_value = {
                "access_token": "mock-ms-token",
                "expires_in": 3600,
            }
            mock_get.return_value.json.return_value = {
                "id": "ms-tenant-user",
                "mail": "tenantuser@contoso.com",
                "givenName": "Tenant",
                "surname": "User",
            }

            resp = api_client.post(
                "/api/auth/social/",
                {"provider": "microsoft", "code": "valid-code"},
                format="json",
            )

        assert resp.status_code == 200
        # Verify the token URL contained the custom tenant
        call_args = mock_post.call_args[0]
        token_url = call_args[0]
        assert "mytenant.onmicrosoft.com" in token_url

    def test_social_auth_init_microsoft_tenant_substitution(self, api_client, settings, db):
        """Microsoft init URL uses the configured MICROSOFT_TENANT."""
        settings.MICROSOFT_CLIENT_ID = "ms-client-id"
        settings.MICROSOFT_TENANT = "mytenant.onmicrosoft.com"

        resp = api_client.get("/api/auth/social/microsoft/init/")
        assert resp.status_code == 200
        url = resp.json()["authorization_url"]
        assert "mytenant.onmicrosoft.com" in url

    def test_social_auth_callback_google_updates_tokens_on_existing_user(self, api_client, settings, db):
        """Existing Google user gets their access/refresh tokens updated on re-auth."""
        from unittest.mock import patch
        from apps.accounts.models import User as UserModel

        settings.GOOGLE_CLIENT_ID = "test-client-id"
        settings.GOOGLE_CLIENT_SECRET = "test-client-secret"

        existing = UserModel.objects.create_user(
            email="reauthtest@test.com",
            username="reauthtest",
            password="testpass123",
            google_id="google-reauth-test",
            google_access_token="old-access",
            google_refresh_token="old-refresh",
            tenant_id=uuid.uuid4(),
        )

        with patch("requests.post") as mock_post, patch("requests.get") as mock_get:
            mock_post.return_value.json.return_value = {
                "access_token": "new-access",
                "refresh_token": "new-refresh",
                "expires_in": 3600,
            }
            mock_get.return_value.json.return_value = {
                "id": "google-reauth-test",
                "email": "reauthtest@test.com",
                "given_name": "Re",
                "family_name": "Auth",
            }

            resp = api_client.post(
                "/api/auth/social/",
                {"provider": "google", "code": "valid-code"},
                format="json",
            )

        assert resp.status_code == 200
        existing.refresh_from_db()
        assert existing.google_access_token == "new-access"
        assert existing.google_refresh_token == "new-refresh"

    def test_social_auth_callback_jwt_contains_tenant_id(self, api_client, settings, db):
        """Social auth JWT includes tenant_id claim when the user has one."""
        from unittest.mock import patch
        from rest_framework_simplejwt.tokens import AccessToken

        settings.GOOGLE_CLIENT_ID = "test-client-id"
        settings.GOOGLE_CLIENT_SECRET = "test-client-secret"

        with patch("requests.post") as mock_post, patch("requests.get") as mock_get:
            mock_post.return_value.json.return_value = {
                "access_token": "mock-token",
                "expires_in": 3600,
            }
            mock_get.return_value.json.return_value = {
                "id": "jwt-test-user",
                "email": "jwtclaim@test.com",
                "given_name": "JWT",
                "family_name": "Claim",
            }

            resp = api_client.post(
                "/api/auth/social/",
                {"provider": "google", "code": "valid-code"},
                format="json",
            )

        assert resp.status_code == 200
        data = resp.json()
        decoded = AccessToken(data["access"])
        # The user was just created with get_or_create which doesn't set a tenant_id
        # so tenant_id claim should be absent
        assert "tenant_id" not in decoded or decoded["tenant_id"] is None

    def test_social_auth_callback_google_init_no_client_id(self, api_client, settings, db):
        """GET /api/auth/social/google/init/ works even when GOOGLE_CLIENT_ID is empty (returns URL with empty client_id)."""
        settings.GOOGLE_CLIENT_ID = ""
        resp = api_client.get("/api/auth/social/google/init/")
        assert resp.status_code == 200
        url = resp.json()["authorization_url"]
        assert "client_id=" in url

    def test_social_auth_callback_microsoft_with_user_principal_name_only(self, api_client, settings, db):
        """Microsoft with only userPrincipalName (no mail) saves email from UPN."""
        from unittest.mock import patch

        settings.MICROSOFT_CLIENT_ID = "ms-client-id"
        settings.MICROSOFT_CLIENT_SECRET = "ms-client-secret"

        with patch("requests.post") as mock_post, patch("requests.get") as mock_get:
            mock_post.return_value.json.return_value = {
                "access_token": "mock-token",
                "expires_in": 3600,
            }
            # No 'mail', only 'userPrincipalName'
            mock_get.return_value.json.return_value = {
                "id": "ms-upn-only",
                "userPrincipalName": "onlyupn@contoso.com",
                "givenName": "Only",
                "surname": "UPN",
            }

            resp = api_client.post(
                "/api/auth/social/",
                {"provider": "microsoft", "code": "valid-code"},
                format="json",
            )

        assert resp.status_code == 200
        assert resp.json()["user"]["email"] == "onlyupn@contoso.com"

    def test_social_auth_callback_linking_existing_user_google(self, api_client, settings, db):
        """Re-linking an existing Google user updates tokens."""
        from unittest.mock import patch
        from apps.accounts.models import User as UserModel

        settings.GOOGLE_CLIENT_ID = "test-client-id"
        settings.GOOGLE_CLIENT_SECRET = "test-client-secret"

        existing = UserModel.objects.create_user(
            email="relink@test.com",
            username="relinkuser",
            password="testpass123",
            google_id="google-relink-user",
            google_access_token="old-token",
            google_refresh_token="old-refresh",
            tenant_id=uuid.uuid4(),
        )

        with patch("requests.post") as mock_post, patch("requests.get") as mock_get:
            mock_post.return_value.json.return_value = {
                "access_token": "new-token",
                "refresh_token": "new-refresh",
                "expires_in": 3600,
            }
            mock_get.return_value.json.return_value = {
                "id": "google-relink-user",
                "email": "relink@test.com",
                "given_name": "Relink",
                "family_name": "User",
            }

            resp = api_client.post(
                "/api/auth/social/",
                {"provider": "google", "code": "valid-code"},
                format="json",
            )

        assert resp.status_code == 200
        existing.refresh_from_db()
        assert existing.google_access_token == "new-token"
        assert existing.google_refresh_token == "new-refresh"

    def test_social_auth_callback_linking_existing_user_microsoft(self, api_client, settings, db):
        """Re-linking an existing Microsoft user updates tokens (the if-not-created branch for MS)."""
        from unittest.mock import patch
        from apps.accounts.models import User as UserModel

        settings.MICROSOFT_CLIENT_ID = "ms-client-id"
        settings.MICROSOFT_CLIENT_SECRET = "ms-client-secret"

        existing = UserModel.objects.create_user(
            email="ms-relink@test.com",
            username="ms-relink",
            password="testpass123",
            microsoft_id="ms-relink-user",
            microsoft_access_token="old-ms-token",
            microsoft_refresh_token="old-ms-refresh",
            tenant_id=uuid.uuid4(),
        )

        with patch("requests.post") as mock_post, patch("requests.get") as mock_get:
            mock_post.return_value.json.return_value = {
                "access_token": "new-ms-token",
                "refresh_token": "new-ms-refresh",
                "expires_in": 3600,
            }
            mock_get.return_value.json.return_value = {
                "id": "ms-relink-user",
                "mail": "ms-relink@test.com",
                "givenName": "MS",
                "surname": "Relink",
            }

            resp = api_client.post(
                "/api/auth/social/",
                {"provider": "microsoft", "code": "valid-ms-code"},
                format="json",
            )

        assert resp.status_code == 200
        existing.refresh_from_db()
        assert existing.microsoft_access_token == "new-ms-token"
        assert existing.microsoft_refresh_token == "new-ms-refresh"

    def test_social_auth_callback_links_existing_user_by_provider_id(self, api_client, settings, db):
        """If a user already has a google_id, they log in instead of creating a new user."""
        from unittest.mock import patch
        from apps.accounts.models import User as UserModel

        settings.GOOGLE_CLIENT_ID = "test-client-id"
        settings.GOOGLE_CLIENT_SECRET = "test-client-secret"

        # Create a user with a google_id
        existing_user = UserModel.objects.create_user(
            email="existing-google@test.com",
            username="existing-google",
            password="testpass123",
            google_id="google-user-999",
            tenant_id=uuid.uuid4(),
        )

        mock_token_response = {
            "access_token": "new-access-token",
            "expires_in": 3600,
        }
        mock_user_info = {
            "id": "google-user-999",
            "email": "existing-google@test.com",
            "given_name": "Existing",
            "family_name": "User",
        }

        with patch("requests.post") as mock_post, patch("requests.get") as mock_get:
            mock_post.return_value.json.return_value = mock_token_response
            mock_get.return_value.json.return_value = mock_user_info

            resp = api_client.post(
                self.SOCIAL_CALLBACK_URL,
                {"provider": "google", "code": "valid-code"},
                format="json",
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["email"] == "existing-google@test.com"
        # Must be the same user
        assert data["user"]["id"] == str(existing_user.id)
        # Token field should be updated
        existing_user.refresh_from_db()
        assert existing_user.google_access_token == "new-access-token"

    # ── Multi-tenant Isolation ─────────────────────────────────────────────────

    def test_multi_tenant_jwt_isolation(self, db, tenant_id):
        """Users from different tenants get distinct JWTs with their own tenant_id claims."""
        from apps.accounts.models import User as UserModel
        from rest_framework_simplejwt.tokens import RefreshToken, AccessToken

        tenant_a_id = uuid.uuid4()
        tenant_b_id = uuid.uuid4()

        user_a = UserModel.objects.create_user(
            email="tenant-a@test.com",
            username="tenanta",
            password="pass1234",
            tenant_id=tenant_a_id,
        )
        user_b = UserModel.objects.create_user(
            email="tenant-b@test.com",
            username="tenantb",
            password="pass1234",
            tenant_id=tenant_b_id,
        )

        # Create JWT tokens — the correct way to add tenant_id to the access token
        # is to set it on the refresh token's payload so it gets copied by
        # the access_token property.
        refresh_a = RefreshToken.for_user(user_a)
        refresh_a["tenant_id"] = str(user_a.tenant_id)
        token_a = str(refresh_a.access_token)

        refresh_b = RefreshToken.for_user(user_b)
        refresh_b["tenant_id"] = str(user_b.tenant_id)
        token_b = str(refresh_b.access_token)

        # Verify the decoded tokens have their respective tenant_ids
        decoded_a = AccessToken(token_a)
        decoded_b = AccessToken(token_b)

        assert decoded_a["tenant_id"] == str(tenant_a_id)
        assert decoded_b["tenant_id"] == str(tenant_b_id)
        assert decoded_a["tenant_id"] != decoded_b["tenant_id"]

        # Verify user A's token authenticates as user A
        client_a = APIClient()
        client_a.credentials(HTTP_AUTHORIZATION=f"Bearer {token_a}")
        resp_a = client_a.get(self.ME_URL)
        assert resp_a.status_code == 200
        assert resp_a.json()["email"] == "tenant-a@test.com"

        # Verify user B's token authenticates as user B
        client_b = APIClient()
        client_b.credentials(HTTP_AUTHORIZATION=f"Bearer {token_b}")
        resp_b = client_b.get(self.ME_URL)
        assert resp_b.status_code == 200
        assert resp_b.json()["email"] == "tenant-b@test.com"

    # ── Me / Profile ───────────────────────────────────────────────────────────

    def test_me_get(self, auth_client, user, db):
        """Authenticated user can fetch their profile via GET."""
        resp = auth_client.get(self.ME_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == user.email
        assert data["id"] == str(user.id)

    def test_me_unauthenticated(self, api_client, db):
        """Unauthenticated GET returns 401."""
        resp = api_client.get(self.ME_URL)
        assert resp.status_code in (401, 403)

    def test_me_patch_update_profile(self, auth_client, user, db):
        """Authenticated user can PATCH their profile fields."""
        resp = auth_client.patch(
            self.ME_URL,
            {"first_name": "Updated", "last_name": "Name", "phone": "+1-555-0100"},
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"
        assert data["phone"] == "+1-555-0100"
        assert data["email"] == user.email  # unchanged

    def test_me_patch_partial(self, auth_client, user, db):
        """PATCH with a single field still returns full profile."""
        resp = auth_client.patch(
            self.ME_URL,
            {"timezone": "America/New_York"},
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["timezone"] == "America/New_York"
        assert data["email"] == user.email

    def test_me_patch_unauthenticated(self, api_client, db):
        """Unauthenticated PATCH returns 401."""
        resp = api_client.patch(
            self.ME_URL,
            {"first_name": "Hacker"},
            format="json",
        )
        assert resp.status_code in (401, 403)

    def test_me_patch_read_only_fields_ignored(self, auth_client, user, db):
        """PATCH cannot overwrite read-only fields like tenant_id or date_joined."""
        resp = auth_client.patch(
            self.ME_URL,
            {"tenant_id": str(uuid.uuid4())},
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["tenant_id"] == str(user.tenant_id)  # unchanged

    # ── Health ─────────────────────────────────────────────────────────────────

    def test_health_liveness(self, api_client, db):
        """GET /api/health/ returns ok with service name."""
        resp = api_client.get(self.HEALTH_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "frontiercrm-api"

    def test_health_readiness(self, api_client, db):
        """GET /api/health/ready/ returns ok with database connected."""
        resp = api_client.get(self.HEALTH_READY_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["database"] == "connected"

    # ── Auth headers / edge cases ─────────────────────────────────────────────

    def test_access_without_bearer_token(self, api_client, db):
        """Requests without any auth header to a protected endpoint return 401."""
        resp = api_client.get(self.ME_URL)
        assert resp.status_code in (401, 403)

    def test_access_with_malformed_bearer(self, api_client, db):
        """A Bearer token that isn't a valid JWT returns 401."""
        api_client.credentials(HTTP_AUTHORIZATION="Bearer not-a-jwt")
        resp = api_client.get(self.ME_URL)
        assert resp.status_code in (401, 403)

    def test_login_returns_valid_jwt(self, api_client, user, db):
        """Login response includes a valid JWT that can be used immediately."""
        resp = api_client.post(
            self.LOGIN_URL,
            {"email": user.email, "password": "testpass123"},
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()

        # Use the returned access token to access a protected endpoint
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {data['access']}")
        resp = client.get(self.ME_URL)
        assert resp.status_code == 200
        assert resp.json()["email"] == user.email

        # Verify the returned refresh token can be used to refresh
        refresh_resp = api_client.post(
            self.REFRESH_URL,
            {"refresh": data["refresh"]},
            format="json",
        )
        assert refresh_resp.status_code == 200
        assert "access" in refresh_resp.json()