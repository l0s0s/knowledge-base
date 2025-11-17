from rest_framework import serializers
from django.conf import settings
from .models import Knowledge, KnowledgeImage


class KnowledgeImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = KnowledgeImage
        fields = ['id', 'image', 'created_at']
        read_only_fields = ['created_at']
    
    def get_image(self, obj):
        """
        Generate image URL with /api/knowledge prefix if needed.
        Uses request.build_absolute_uri() to get the full URL with prefix.
        """
        if not obj.image:
            return None
        
        request = self.context.get('request')
        if request:
            # Get the image URL from the model field
            image_url = obj.image.url
            
            # Check if SCRIPT_NAME is set (by PrefixMiddleware) to include prefix
            script_name = request.META.get('SCRIPT_NAME', '')
            if script_name:
                # SCRIPT_NAME already includes the prefix, build_absolute_uri will use it
                return request.build_absolute_uri(image_url)
            else:
                # Fallback: use FORCE_SCRIPT_NAME from settings
                prefix = getattr(settings, 'FORCE_SCRIPT_NAME', '')
                if prefix and not image_url.startswith(prefix):
                    prefix = prefix.rstrip('/')
                    if image_url.startswith('/'):
                        # Build absolute URI with prefix
                        return request.build_absolute_uri(f"{prefix}{image_url}")
                return request.build_absolute_uri(image_url)
        else:
            # Fallback: manually add prefix if FORCE_SCRIPT_NAME is set
            prefix = getattr(settings, 'FORCE_SCRIPT_NAME', '')
            image_url = obj.image.url
            if prefix and not image_url.startswith(prefix):
                # Ensure prefix doesn't have trailing slash and image_url starts with /
                prefix = prefix.rstrip('/')
                if image_url.startswith('/'):
                    return f"{prefix}{image_url}"
            return image_url


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
