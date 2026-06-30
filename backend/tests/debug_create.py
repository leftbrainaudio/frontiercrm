"""Debug the 400 response from test_create."""
import os, uuid, django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

UserModel = get_user_model()

tenant_id = uuid.uuid4()
user = UserModel.objects.create_user(
    email=f"debug-{uuid.uuid4().hex[:8]}@test.com",
    username=f"debug-{uuid.uuid4().hex[:8]}",
    password="testpass123",
    tenant_id=tenant_id,
    google_refresh_token="fake-refresh-token",
    google_access_token="fake-access-token",
)

client = APIClient()
refresh = RefreshToken.for_user(user)
refresh.access_token["tenant_id"] = str(user.tenant_id)
client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

payload = {
    "to_emails": ["recipient@example.com"],
    "subject": "Hello from CRM",
    "body_text": "This is a test",
}

resp = client.post("/api/emails/", payload, format="json")
print(f"Status: {resp.status_code}")
print(f"Response: {resp.json()}")