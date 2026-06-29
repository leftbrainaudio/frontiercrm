from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contacts', '0001_initial'),
        ('pipelines', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SyncConnection',
            fields=[
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('tenant_id', models.UUIDField(db_index=True, help_text='UUID of the tenant this record belongs to')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('provider', models.CharField(choices=[('gmail', 'Gmail'), ('outlook', 'Outlook'), ('google_calendar', 'Google Calendar'), ('outlook_calendar', 'Outlook Calendar'), ('imap', 'IMAP'), ('caldav', 'CalDAV')], max_length=32)),
                ('provider_account', models.CharField(help_text='Email address or account identifier', max_length=256)),
                ('account_type', models.CharField(choices=[('personal', 'Personal'), ('shared', 'Shared'), ('resource', 'Resource')], default='personal', max_length=16)),
                ('access_token_encrypted', models.TextField(blank=True, default='')),
                ('refresh_token_encrypted', models.TextField(blank=True, default='')),
                ('token_expires_at', models.DateTimeField(blank=True, null=True)),
                ('scopes', models.JSONField(blank=True, default=list)),
                ('is_active', models.BooleanField(default=True)),
                ('last_sync_at', models.DateTimeField(blank=True, null=True)),
                ('last_sync_success', models.BooleanField(null=True)),
                ('last_error_message', models.TextField(blank=True, default='')),
                ('error_count', models.IntegerField(default=0)),
                ('status', models.CharField(choices=[('active', 'Active'), ('error', 'Error'), ('expired', 'Expired'), ('disconnected', 'Disconnected'), ('pending', 'Pending')], default='active', max_length=16)),
                ('sync_interval_seconds', models.IntegerField(default=60)),
                ('watch_expires_at', models.DateTimeField(blank=True, null=True)),
                ('watch_history_id', models.BigIntegerField(blank=True, null=True)),
                ('gcp_project_id', models.CharField(blank=True, default='', max_length=256)),
                ('encryption_key_id', models.UUIDField(blank=True, null=True)),
                ('last_history_id_synced', models.BigIntegerField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sync_connections', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'sync_connections',
            },
        ),
        migrations.CreateModel(
            name='TenantEncryptionKey',
            fields=[
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tenant_id', models.UUIDField(db_index=True, unique=True)),
                ('key_data', models.BinaryField()),
                ('key_version', models.IntegerField(default=1)),
                ('rotated_at', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'tenant_encryption_keys',
            },
        ),
        migrations.CreateModel(
            name='SyncConflict',
            fields=[
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('tenant_id', models.UUIDField(db_index=True, help_text='UUID of the tenant this record belongs to')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('entity_type', models.CharField(max_length=32)),
                ('entity_id', models.UUIDField(blank=True, null=True)),
                ('external_id', models.CharField(blank=True, default='', max_length=512)),
                ('conflict_type', models.CharField(choices=[('concurrent_edit', 'Concurrent Edit'), ('deleted_elsewhere', 'Deleted Elsewhere'), ('version_mismatch', 'Version Mismatch')], max_length=32)),
                ('resolution_strategy', models.CharField(choices=[('last_write_wins', 'Last Write Wins'), ('provider_wins', 'Provider Wins'), ('crm_wins', 'CRM Wins'), ('manual', 'Manual')], max_length=32)),
                ('crm_version', models.JSONField(blank=True, default=dict)),
                ('provider_version', models.JSONField(blank=True, default=dict)),
                ('resolved_data', models.JSONField(blank=True, default=dict)),
                ('resolved_by', models.CharField(choices=[('system', 'System'), ('user', 'User')], default='system', max_length=32)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('connection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conflicts', to='sync.syncconnection')),
            ],
            options={
                'db_table': 'sync_conflicts',
            },
        ),
        migrations.CreateModel(
            name='EmailThread',
            fields=[
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('tenant_id', models.UUIDField(db_index=True, help_text='UUID of the tenant this record belongs to')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('subject', models.CharField(blank=True, default='', max_length=512)),
                ('normalized_subject', models.CharField(blank=True, default='', max_length=512)),
                ('participants', models.JSONField(blank=True, default=list)),
                ('last_email_at', models.DateTimeField(blank=True, null=True)),
                ('email_count', models.IntegerField(default=0)),
                ('is_archived', models.BooleanField(default=False)),
                ('account', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='email_threads', to='contacts.account')),
                ('contact', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='email_threads', to='contacts.contact')),
                ('deal', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='email_threads', to='pipelines.deal')),
            ],
            options={
                'db_table': 'email_threads',
            },
        ),
        migrations.CreateModel(
            name='SyncState',
            fields=[
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('tenant_id', models.UUIDField(db_index=True, help_text='UUID of the tenant this record belongs to')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('sync_type', models.CharField(choices=[('email', 'Email'), ('calendar_event', 'Calendar Event'), ('contacts', 'Contacts')], max_length=32)),
                ('provider', models.CharField(max_length=32)),
                ('cursor_data', models.JSONField(blank=True, default=dict)),
                ('last_full_sync_at', models.DateTimeField(blank=True, null=True)),
                ('last_delta_sync_at', models.DateTimeField(blank=True, null=True)),
                ('next_sync_at', models.DateTimeField(blank=True, null=True)),
                ('sync_batch_size', models.IntegerField(default=100)),
                ('state', models.CharField(choices=[('pending', 'Pending'), ('syncing', 'Syncing'), ('complete', 'Complete'), ('error', 'Error'), ('needs_full_resync', 'Needs Full Resync')], default='pending', max_length=24)),
                ('error_details', models.TextField(blank=True, default='')),
                ('total_synced_count', models.IntegerField(default=0)),
                ('total_deleted_count', models.IntegerField(default=0)),
                ('sync_duration_ms', models.IntegerField(blank=True, null=True)),
                ('connection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sync_states', to='sync.syncconnection')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sync_states', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'sync_states',
                'indexes': [models.Index(fields=['next_sync_at'], name='sync_states_next_sy_34cfbf_idx'), models.Index(fields=['tenant_id', 'user'], name='sync_states_tenant__20cfc3_idx')],
            },
        ),
        migrations.AddConstraint(
            model_name='syncstate',
            constraint=models.UniqueConstraint(fields=('connection', 'sync_type'), name='uq_sync_state'),
        ),
        migrations.AddIndex(
            model_name='syncconnection',
            index=models.Index(fields=['tenant_id', 'user'], name='sync_connec_tenant__612484_idx'),
        ),
        migrations.AddIndex(
            model_name='syncconnection',
            index=models.Index(fields=['tenant_id', 'provider'], name='sync_connec_tenant__100c52_idx'),
        ),
        migrations.AddIndex(
            model_name='syncconnection',
            index=models.Index(fields=['status'], name='sync_connec_status_c5f950_idx'),
        ),
        migrations.AddIndex(
            model_name='syncconnection',
            index=models.Index(fields=['is_active'], name='sync_connec_is_acti_95dfba_idx'),
        ),
        migrations.AddConstraint(
            model_name='syncconnection',
            constraint=models.UniqueConstraint(fields=('tenant_id', 'user', 'provider', 'provider_account'), name='uq_sync_connection'),
        ),
        migrations.AddIndex(
            model_name='syncconflict',
            index=models.Index(fields=['tenant_id', 'entity_type', 'entity_id'], name='sync_confli_tenant__9b30d5_idx'),
        ),
        migrations.AddIndex(
            model_name='syncconflict',
            index=models.Index(fields=['connection'], name='sync_confli_connect_288980_idx'),
        ),
        migrations.AddIndex(
            model_name='syncconflict',
            index=models.Index(fields=['resolved_at'], name='sync_confli_resolve_ea721f_idx'),
        ),
        migrations.AddIndex(
            model_name='emailthread',
            index=models.Index(fields=['tenant_id'], name='email_threa_tenant__9aebb2_idx'),
        ),
        migrations.AddIndex(
            model_name='emailthread',
            index=models.Index(fields=['contact'], name='email_threa_contact_4e273b_idx'),
        ),
        migrations.AddIndex(
            model_name='emailthread',
            index=models.Index(fields=['deal'], name='email_threa_deal_id_b8c224_idx'),
        ),
        migrations.AddIndex(
            model_name='emailthread',
            index=models.Index(fields=['tenant_id', 'normalized_subject'], name='email_threa_tenant__d84c1a_idx'),
        ),
        migrations.AddIndex(
            model_name='emailthread',
            index=models.Index(fields=['tenant_id', 'last_email_at'], name='email_threa_tenant__297037_idx'),
        ),
    ]
