"""
Brief: Django tests.py file.

Description: This file contains the tests for the Django core app.

Author: Divij Sharma <divijs75@gmail.com>
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='qwerty@12345',
        first_name='Test',
        last_name='User'
    )


@pytest.fixture
def admin_user():
    user = User.objects.create_superuser(
        username='adminuser',
        email='adminuser@example.com',
        password='qwerty@12345',
        first_name='Admin',
        last_name='User'
    )
    return user


@pytest.mark.django_db
def test_user_creation(api_client):
    url = reverse('user-list')
    data = {
        'first_name': 'New',
        'last_name': 'User',
        'email': 'newuser@example.com',
        'username': 'newuser',
        'password': 'qwerty@12345'
    }
    response = api_client.post(url, data, format='json')
    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.filter(username='newuser').exists()


@pytest.mark.django_db
def test_check_username_exists(api_client, user):
    url = reverse('exists')
    response = api_client.post(url, {'username': 'testuser'}, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'username_exists': True}

    response = api_client.post(url, {'username': 'nonexistentuser'}, format='json')
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'username_exists': False}


@pytest.mark.django_db
def test_home(api_client):
    url = reverse('home')
    response = api_client.get(url)
    print(response.data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_custom_token_obtain(api_client, user):
    user.is_active = True
    user.save()
    url = reverse('custom_jwt_create')
    data = {
        'username': 'testuser',
        'password': 'qwerty@12345'
    }
    response = api_client.post(url, data, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert 'access' in response.json()
    assert 'refresh' in response.json()


@pytest.mark.django_db
def test_user_deactivation(api_client, admin_user):
    url = reverse('user-list')
    data = {
        'username': 'testuser2',
        'email': 'testuser2@example.com',
        'password': 'qwerty@12345',
        'first_name': 'Test',
        'last_name': 'User'
    }
    api_client.post(url, data, format='json')
    user = User.objects.get(username='testuser2')
    assert user.is_deactivated is False
    assert user.is_active is False


@pytest.mark.django_db
def test_user_activation(api_client, user):
    user.is_active = True
    user.is_deactivated = True
    user.save()
    print(user.is_deactivated)
    print(user.is_active)
    assert user.is_deactivated is True
    assert user.is_active is True
