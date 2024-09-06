"""
Brief: Django tests.py file.

Description: This file contains the tests for the Django data app.

Author: Divij Sharma <divijs75@gmail.com>
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
from .models import Skeleton, Field
from live.models import Instance
from django.contrib.auth import get_user_model


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
def skeleton(instance):
    return Skeleton.objects.create(
        instance=instance,
        title='Test Form',
        description='Test Description',
        endMessage='Test End Message'
    )


@pytest.fixture
def field(skeleton):
    return Field.objects.create(
        skeleton=skeleton,
        title='Test Question',
        type='text',
        required=True
    )


@pytest.mark.django_db
def test_form_list_create(api_client, instance, user):
    api_client.force_authenticate(user=user)
    response = api_client.post(reverse('form-list-create', kwargs={'hash': instance.hash}), data={
        'title': 'New Form',
        'description': 'New Description',
        'endMessage': 'New End Message',
        'fields': [
            {
                'title': 'Short text question',
                'type': 'short-text',
                'required': True
            }
        ]
    }, format='json')
    assert response.status_code == status.HTTP_201_CREATED
    assert Skeleton.objects.count() == 1
    assert Skeleton.objects.filter(title='New Form').exists()
    assert Field.objects.count() == 1
    assert Field.objects.filter(title='Short text question').exists()

    response = api_client.get(reverse('form-list-create', kwargs={'hash': instance.hash}))

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]['title'] == 'New Form'
    assert data[0]['description'] == 'New Description'
    assert data[0]['endMessage'] == 'New End Message'
    assert data[0]['fields'][0]['title'] == 'Short text question'
    assert data[0]['fields'][0]['type'] == 'short-text'
    assert data[0]['fields'][0]['required'] is True


@pytest.mark.django_db
def test_form_detail(api_client, instance, skeleton, user):
    api_client.force_authenticate(user=user)
    response = api_client.get(reverse('form-detail', kwargs={'hash': instance.hash, 'pk': skeleton.pk}))
    assert response.status_code == status.HTTP_200_OK
    assert response.data['title'] == skeleton.title

    update_data = {
        'title': 'Updated Form Title',
        'description': 'Updated Description',
        'endMessage': 'Updated End Message',
    }
    response = api_client.patch(reverse(
        'form-detail', kwargs={'hash': instance.hash, 'pk': skeleton.pk}), data=update_data, format='json'
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data['title'] == 'Updated Form Title'
    assert response.data['description'] == 'Updated Description'
    assert response.data['endMessage'] == 'Updated End Message'

    response = api_client.delete(reverse('form-detail', kwargs={'hash': instance.hash, 'pk': skeleton.pk}))
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Skeleton.objects.filter(pk=skeleton.pk).exists()


@pytest.mark.django_db
def test_question_list_create(api_client, instance, skeleton, user):
    api_client.force_authenticate(user=user)
    response = api_client.post(
        reverse('question-list-create', kwargs={'hash': instance.hash, 'pk': skeleton.pk}), data={
            'title': 'New Question',
            'type': 'short-text',
            'required': True
        }, format='json'
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['type'] == 'short-text'
    assert Field.objects.count() == 1

    response = api_client.post(
        reverse('question-list-create', kwargs={'hash': instance.hash, 'pk': skeleton.pk}), data={
            'title': 'New Question',
            'type': 'long-text',
            'required': True
        }, format='json'
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['type'] == 'long-text'
    assert Field.objects.count() == 2

    response = api_client.post(
        reverse('question-list-create', kwargs={'hash': instance.hash, 'pk': skeleton.pk}), data={
            'title': 'New Question',
            'type': 'number',
            'required': True
        }, format='json'
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['type'] == 'number'
    assert Field.objects.count() == 3

    response = api_client.post(
        reverse('question-list-create', kwargs={'hash': instance.hash, 'pk': skeleton.pk}), data={
            'title': 'New Question',
            'type': 'multioption-singleanswer',
            'options': [
                'a',
                'b',
                'c',
                'd'
            ],
            'required': True
        }, format='json'
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['type'] == 'multioption-singleanswer'
    assert response.data['options'] == ['a', 'b', 'c', 'd']
    assert Field.objects.count() == 4

    response = api_client.post(
        reverse('question-list-create', kwargs={'hash': instance.hash, 'pk': skeleton.pk}), data={
            'title': 'New Question',
            'type': 'multioption-multianswer',
            'options': [
                'a',
                'b',
                'c',
                'd'
            ],
            'required': True
        }, format='json'
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['type'] == 'multioption-multianswer'
    assert response.data['options'] == ['a', 'b', 'c', 'd']
    assert Field.objects.count() == 5

    response = api_client.post(
        reverse('question-list-create', kwargs={'hash': instance.hash, 'pk': skeleton.pk}), data={
            'title': 'New Question',
            'type': 'file',
            'accepted': [
                'jpg',
                'png',
                'jpeg',
                'pdf',
                'txt'
            ],
            'required': True
        }, format='json'
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data['type'] == 'file'
    assert Field.objects.count() == 6

    response = api_client.get(reverse('question-list-create', kwargs={'hash': instance.hash, 'pk': skeleton.pk}))
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 6
    assert data[0]['type'] == 'short-text'
    assert data[1]['type'] == 'long-text'
    assert data[2]['type'] == 'number'
    assert data[3]['type'] == 'multioption-singleanswer'
    assert data[4]['type'] == 'multioption-multianswer'
    assert data[5]['type'] == 'file'


@pytest.mark.django_db
def test_question_detail(api_client, instance, skeleton, field, user):
    api_client.force_authenticate(user=user)

    response = api_client.get(
        reverse('question-detail', kwargs={'hash': instance.hash, 'pk': skeleton.pk, 'itempk': field.pk})
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data['title'] == field.title

    update_data = {
        'title': 'Updated Question Title',
        'type': 'short-text',
        'required': False
    }
    response = api_client.patch(
        reverse('question-detail', kwargs={'hash': instance.hash, 'pk': skeleton.pk, 'itempk': field.pk}),
        data=update_data, format='json'
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data['title'] == 'Updated Question Title'
    assert response.data['type'] == 'short-text'
    assert response.data['required'] is False

    response = api_client.delete(
        reverse('question-detail', kwargs={'hash': instance.hash, 'pk': skeleton.pk, 'itempk': field.pk})
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Field.objects.filter(pk=field.pk).exists()


@pytest.mark.django_db
def test_response_list_create(api_client, instance, user):
    api_client.force_authenticate(user=user)
    response = api_client.get(reverse('response-list-create', kwargs={'hash': instance.hash}))
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_custom_get_method(api_client, instance, user):
    api_client.force_authenticate(user=user)
    response = api_client.get(reverse('form-get', kwargs={'hash': instance.hash}))
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_custom_post__get_method(api_client, instance, user, field):
    api_client.force_authenticate(user=user)
    response = api_client.post(reverse('form-post', kwargs={'hash': instance.hash}), data={
            'answers': [{'id': field.pk, 'value': 'Test Answer'}]
        }, format='json'
    )
    assert response.status_code == status.HTTP_201_CREATED
