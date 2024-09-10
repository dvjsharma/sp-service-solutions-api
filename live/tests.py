"""
Brief: Django tests.py file.

Description: This file contains the tests for the Django Live app

Author: Divij Sharma <divijs75@gmail.com>
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from .models import Instance, SocialUser


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    User = get_user_model()
    return User.objects.create_user(username='testuser', password='testpassword')


@pytest.fixture
def instance(user):
    return Instance.objects.create(
        user=user,
        name='test_instance',
        description='test_description',
    )


@pytest.fixture
def social_user(instance):
    return SocialUser.objects.create(
        instance=instance,
        user_social_type=0x1 << 0,
        first_name='Test',
        last_name='User',
        username='testuser',
        password='testpassword'
    )


@pytest.fixture
def social_user_csv(instance):
    return SocialUser.objects.create(
        instance=instance,
        user_social_type=0x1 << 1,
        first_name='Test',
        last_name='User',
        username='testuser',
        password='testpassword'
    )


@pytest.mark.django_db
def test_instance_list_create(api_client, user):
    api_client.force_authenticate(user=user)
    response = api_client.get(reverse('instance-list-create'))
    assert response.status_code == status.HTTP_200_OK

    data = {
        'name': 'test_instance',
        'description': 'test_description',
    }
    response = api_client.post(reverse('instance-list-create'), data, format='json')
    hash = response.data['hash']
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['hash'] == hash
    assert response.data['name'] == 'test_instance'
    assert response.data['description'] == 'test_description'
    assert response.data['instance_status'] == 0x1 << 1
    assert response.data['instance_auth_type'] == 0x1 << 0


@pytest.mark.django_db
def test_instance_retrieve_update_destroy(api_client, user, instance):
    api_client.force_authenticate(user=user)
    response = api_client.get(reverse('instance-detail', args=[instance.hash]))
    assert response.status_code == status.HTTP_200_OK
    assert response.data['hash'] == instance.hash
    assert response.data['name'] == instance.name
    assert response.data['description'] == instance.description
    assert response.data['instance_status'] == instance.instance_status
    assert response.data['instance_auth_type'] == instance.instance_auth_type

    data = {
        'name': 'updated_name',
        'description': 'updated_description',
        'instance_auth_type': 0x1 << 2,
        'instance_status': 0x1 << 0,
    }
    response = api_client.patch(reverse('instance-detail', args=[instance.hash]), data, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['hash'] == instance.hash
    assert response.data['name'] == 'updated_name'
    assert response.data['description'] == 'updated_description'
    assert response.data['instance_status'] == 0x1 << 0
    assert response.data['instance_auth_type'] == 0x1 << 2

    response = api_client.delete(reverse('instance-detail', args=[instance.hash]))
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert Instance.objects.count() == 0


@pytest.mark.django_db
def test_instance_type_status(api_client, instance):
    response = api_client.post(reverse('instance-status'), {'hash': instance.hash}, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['instance_status'] == 0x1 << 1


@pytest.mark.django_db
def test_instance_csv_view(api_client, user, instance):
    api_client.force_authenticate(user=user)

    from io import BytesIO
    import pandas as pd

    api_client.force_authenticate(user=user)
    csv_data = BytesIO(b"firstname,lastname,uname,pwd\nTest,Name,testname,secret")
    response = api_client.post(
        reverse('instance-csv-post', args=[instance.hash]),
        {
            'first_name': 'firstname',
            'last_name': 'lastname',
            'username': 'uname',
            'password': 'pwd',
            'file': csv_data
        },
        format='multipart'
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["message"] == "Users added successfully"
    assert SocialUser.objects.count() == 1

    response = api_client.get(reverse('instance-csv', args=[instance.hash, 'testname']))
    assert response.status_code == status.HTTP_200_OK
    assert response.data['user_social_type'] == 0x1 << 1
    assert response.data['first_name'] == 'Test'
    assert response.data['last_name'] == 'Name'
    assert response.data['username'] == 'testname'
    assert response.data['has_voted'] is False

    response = api_client.get('/api/v1/live/instance/CSV/{hash}/download'.format(hash=instance.hash))
    assert response.status_code == status.HTTP_200_OK
    df = pd.read_csv(BytesIO(response.content))
    assert df.shape[0] == 1


@pytest.mark.django_db
def test_instance_json_view(api_client, user, instance):
    api_client.force_authenticate(user=user)

    from io import StringIO
    import json

    json_data = StringIO('[{"firstname": "Test", "lastname": "Name", "uname": "testname", "pwd": "secret"}]')
    response = api_client.post(
        reverse('instance-json-post', args=[instance.hash]),
        {
            'first_name': 'firstname',
            'last_name': 'lastname',
            'username': 'uname',
            'password': 'pwd',
            'file': json_data
        },
        format='multipart'
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["message"] == "Users added successfully"
    assert SocialUser.objects.count() == 1

    response = api_client.get(reverse('instance-json', args=[instance.hash, 'testname']))
    assert response.status_code == status.HTTP_200_OK
    data = json.loads(response.content)
    assert len(data) == 7
    assert data['first_name'] == 'Test'
    assert data['last_name'] == 'Name'
    assert data['username'] == 'testname'
    assert data['has_voted'] is False

    response = api_client.get('/api/v1/live/instance/CSV/{hash}/download'.format(hash=instance.hash))
    assert response.status_code == status.HTTP_200_OK
    assert len(data) == 7


@pytest.mark.django_db
def test_instance_organization_view(api_client, user, social_user, instance):
    api_client.force_authenticate(user=user)

    response = api_client.get(reverse('instance-orgs', args=[instance.hash]))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]['first_name'] == 'Test'
    assert response.data[0]['last_name'] == 'User'
    assert response.data[0]['username'] == 'testuser'
    assert response.data[0]['user_social_type'] == 0x1 << 0
    assert response.data[0]['has_voted'] is False

    response = api_client.get(reverse('instance-orgs', args=[instance.hash]) + 'download?format=json')
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_social_user_token_obtain_pair(api_client, instance, social_user_csv):

    from django.contrib.auth.hashers import make_password

    assert SocialUser.objects.filter(username=social_user_csv.username, instance=instance).exists()
    social_user_csv.password = make_password('testpassword')
    social_user_csv.save()
    response = api_client.post(reverse('instance-login', args=[instance.hash]), {
        'username': social_user_csv.username,
        'password': 'testpassword'
    }, format='json')
    assert response.status_code == status.HTTP_201_CREATED
    assert 'access' in response.data


@pytest.mark.django_db
def test_provider_auth_view(api_client):
    response = api_client.get(reverse('provider-auth', args=['1849b35954104c3c', 'google-oauth2'])
                              + '?redirect_uri=http://localhost:3000')
    assert response.status_code == status.HTTP_200_OK
    assert 'authorization_url' in response.data
