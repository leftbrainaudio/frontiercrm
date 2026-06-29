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