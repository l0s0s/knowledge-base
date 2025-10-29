from django.contrib import admin
from .models import Knowledge, KnowledgeImage


class KnowledgeImageInline(admin.TabularInline):
    model = KnowledgeImage
    extra = 1
    fields = ('image', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Knowledge)
class KnowledgeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'text_preview', 'quiz', 'created_at', 'updated_at', 'is_deleted')
    list_filter = ('created_at', 'updated_at', 'deleted_at', 'user_id')
    search_fields = ('user_id', 'text')
    readonly_fields = ('created_at', 'updated_at', 'deleted_at')
    inlines = [KnowledgeImageInline]

    fieldsets = (
        ('Content', {
            'fields': ('user_id', 'text', 'quiz')
        }),
        ('Images', {
            'fields': (),
            'description': 'Add images using the inline editor below'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )

    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Text'

    def is_deleted(self, obj):
        return obj.deleted_at is not None
    is_deleted.boolean = True
    is_deleted.short_description = 'Deleted'

    actions = ['restore_selected']

    def restore_selected(self, request, queryset):
        for obj in queryset:
            obj.restore()
        self.message_user(request, f'{queryset.count()} knowledge entries restored.')
    restore_selected.short_description = 'Restore selected entries'


@admin.register(KnowledgeImage)
class KnowledgeImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'knowledge', 'image', 'created_at')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)
