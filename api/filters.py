import django_filters
from .models import Knowledge


class KnowledgeFilter(django_filters.FilterSet):
    user_id = django_filters.CharFilter(field_name='user_id', lookup_expr='exact')
    text__icontains = django_filters.CharFilter(field_name='text', lookup_expr='icontains')
    created_at__gte = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at__lte = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    updated_at__gte = django_filters.DateTimeFilter(field_name='updated_at', lookup_expr='gte')
    updated_at__lte = django_filters.DateTimeFilter(field_name='updated_at', lookup_expr='lte')

    class Meta:
        model = Knowledge
        fields = ['user_id', 'text', 'created_at', 'updated_at']
