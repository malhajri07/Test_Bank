# Generated manually for EmailVerificationToken model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0002_customuser_role'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailVerificationToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(help_text='Unique token for email verification', max_length=64, unique=True, verbose_name='Verification Token')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('expires_at', models.DateTimeField(help_text='Token expiration time (default: 7 days)', verbose_name='Expires At')),
                ('is_used', models.BooleanField(default=False, help_text='Whether this token has been used', verbose_name='Is Used')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='email_verification', to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'Email Verification Token',
                'verbose_name_plural': 'Email Verification Tokens',
                'ordering': ['-created_at'],
            },
        ),
    ]
