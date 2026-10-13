import json

from django.contrib.auth.models import User
from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers
from rest_framework_mongoengine import serializers as mongoserializers

from core.messages import ErrorMessages
from core.models import Creator, Document
from core.models import DocumentTag, EmailRelayLog
from core.models import Profile
from core.mongo import ExpenseDocument
from core.utils import deep_get, safeget

class NestedModelSerializer(serializers.ModelSerializer):

    def nested_update(self, instance, validated_data):
        serializer_fields = self._writable_fields

        for serializer_field in serializer_fields:
            if not (serializer_field.field_name in validated_data): 
                continue

            if not hasattr(serializer_field, 'fields'):
                attribute = serializer_field.field_name
                setattr(instance, attribute, safeget(validated_data, attribute))
                continue

            _sub_instance = getattr(instance, serializer_field.field_name)
            _data_label = ''
            for attribute in serializer_field.fields:
                _data_label = serializer_field.field_name + '.' + attribute
                if deep_get(validated_data, _data_label):
                    setattr(_sub_instance, attribute, deep_get(validated_data, _data_label))
            _sub_instance.save()
        
        instance.save()
        return instance


class CreatorSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Creator
        fields = '__all__'


class DocumentTagSerializer(serializers.ModelSerializer):
    document = serializers.PrimaryKeyRelatedField(many=False, read_only=True)
    
    def create(self, validated_data):
        doc_id = self.context.get('request').parser_context.get('kwargs').get('doc_pk')
        validated_data['document_id'] = doc_id
        return super().create(validated_data)
    
    class Meta:
        model = DocumentTag
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'date_joined', 'profile', 'stats']
        depth = 1


class DocSerializer(mongoserializers.DocumentSerializer):
    class Meta:
        model = ExpenseDocument
        fields = '__all__'


class DocumentSerializer(NestedModelSerializer):

    class Meta:
        model = Document
        fields = '__all__'
        depth = 1


class EmailRelayLogSerializer(serializers.ModelSerializer):

    class Meta:
        model = EmailRelayLog
        fields = '__all__'


class ProfileSerializer(serializers.ModelSerializer):
    notifications_allowed = serializers.BooleanField(required=False)
    analytics_allowed = serializers.BooleanField(required=False)
    
    class Meta:
        model = Profile
        fields = [
            'user',
            'email_relay',
            'notifications_allowed',
            'analytics_allowed',
            'postal_code',
        ]
        read_only_fields = ['user']
        extra_kwargs={
            'notifications_allowed': { 'required': True, 'allow_null': False },
            'analytics_allowed': { 'required': True, 'allow_null': False}
        }


class ProfileServiceSerializer(serializers.ModelSerializer):
    """Fields the email Lambda needs. Storage bucket names stay off the user-facing serializer."""

    class Meta:
        model = Profile
        fields = ['user', 'storage_bucket']
        read_only_fields = ['user', 'storage_bucket']
   
