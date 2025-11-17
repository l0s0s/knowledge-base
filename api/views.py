from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import Knowledge, KnowledgeImage
from .serializers import (
    KnowledgeSerializer,
    KnowledgeCreateSerializer,
    KnowledgeUpdateSerializer,
    KnowledgeImageSerializer
)
from .filters import KnowledgeFilter


class KnowledgeViewSet(viewsets.ModelViewSet):
    queryset = Knowledge.objects.filter(deleted_at__isnull=True)
    filterset_class = KnowledgeFilter
    ordering_fields = ['created_at', 'updated_at', 'user_id']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return KnowledgeCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return KnowledgeUpdateSerializer
        return KnowledgeSerializer

    def get_queryset(self):
        queryset = Knowledge.objects.filter(deleted_at__isnull=True)
        return queryset

    def perform_destroy(self, instance):
        instance.soft_delete()

    @extend_schema(
        summary="Restore deleted knowledge entry",
        description="Restore a soft-deleted knowledge entry by setting deleted_at to null",
        responses={200: KnowledgeSerializer, 400: None, 404: None}
    )
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        try:
            knowledge = Knowledge.objects.get(pk=pk)
        except Knowledge.DoesNotExist:
            return Response(
                {'detail': 'Knowledge entry not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if knowledge.deleted_at is None:
            return Response(
                {'detail': 'Knowledge entry is not deleted.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        knowledge.restore()
        serializer = self.get_serializer(knowledge)
        return Response(serializer.data)

    @extend_schema(
        summary="Upload image for knowledge entry",
        description="Upload an image file to associate with a knowledge entry",
        request={"multipart/form-data": {"type": "object", "properties": {"image": {"type": "string", "format": "binary"}}}},
        responses={201: KnowledgeImageSerializer, 400: None, 404: None}
    )
    @action(detail=True, methods=['post'], url_path='upload-image')
    def upload_image(self, request, pk=None):
        knowledge = self.get_object()
        if 'image' not in request.FILES:
            return Response(
                {'detail': 'Image file is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        image_file = request.FILES['image']
        image = KnowledgeImage.objects.create(
            knowledge=knowledge,
            image=image_file
        )
        serializer = KnowledgeImageSerializer(image, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Delete image from knowledge entry",
        description="Delete a specific image associated with a knowledge entry",
        parameters=[
            OpenApiParameter(name='image_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description='Image ID to delete')
        ],
        responses={204: None, 404: None}
    )
    @action(detail=True, methods=['delete'], url_path='images/(?P<image_id>[^/.]+)')
    def delete_image(self, request, pk=None, image_id=None):
        knowledge = self.get_object()
        try:
            image = knowledge.images.get(id=image_id)
            image.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except KnowledgeImage.DoesNotExist:
            return Response(
                {'detail': 'Image not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
