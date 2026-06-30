"""Debug failing test responses."""
import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.development'
django.setup()
from django.test.utils import setup_test_environment
setup_test_environment()

from rest_framework.test import APIClient
from apps.accounts.models import User as UserModel
import uuid

u = UserModel.objects.create_user(
    username='tester123',
    email='tester@test.com',
    password='testpass123',
    tenant_id=uuid.uuid4()
)
client = APIClient()
from rest_framework_simplejwt.tokens import RefreshToken
refresh = RefreshToken.for_user(u)
refresh.access_token['tenant_id'] = str(u.tenant_id)
client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

from tests.test_email import compose_payload
payload = compose_payload()
resp = client.post('/api/emails/', payload, format='json')
print('Status:', resp.status_code)
raw = resp.content.decode()
print('Raw content:', repr(raw))
import json
try:
    data = json.loads(raw)
    print('Decoded:', json.dumps(data, indent=2))
except json.JSONDecodeError:
    print('Not valid JSON')
