from rest_framework import serializers
from .models import Knowledge, KnowledgeImage


class KnowledgeImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeImage
        fields = ['id', 'image', 'created_at']
        read_only_fields = ['created_at']


class KnowledgeSerializer(serializers.ModelSerializer):
    images = KnowledgeImageSerializer(many=True, read_only=True)

    class Meta:
        model = Knowledge
        fields = ['id', 'user_id', 'text', 'quiz', 'images', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
        ref_name = 'Knowledge'


class KnowledgeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Knowledge
        fields = ['user_id', 'text', 'quiz']
        
    def validate_quiz(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Quiz must be a list.")
        return value


class KnowledgeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Knowledge
        fields = ['text', 'quiz']
        
    def validate_quiz(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Quiz must be a list.")
        return value
