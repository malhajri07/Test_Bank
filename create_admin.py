#!/usr/bin/env python
"""
Script to create a Django superuser non-interactively.
Run this script to create an admin user.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'testbank_platform.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Create superuser
username = 'admin'
email = 'admin@testbank.com'
password = 'admin123'

if User.objects.filter(username=username).exists():
    print(f'User "{username}" already exists!')
    user = User.objects.get(username=username)
    user.set_password(password)
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print(f'Updated existing user "{username}" with new password.')
else:
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f'Superuser "{username}" created successfully!')

print(f'\nAdmin Login Credentials:')
print(f'Username: {username}')
print(f'Password: {password}')
print(f'\nAccess admin panel at: http://127.0.0.1:8000/admin/')

