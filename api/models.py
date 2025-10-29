from django.db import models
from django.utils import timezone


class Knowledge(models.Model):
    user_id = models.CharField(max_length=255, db_index=True)
    text = models.TextField()
    quiz = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def restore(self):
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])

    @property
    def is_deleted(self):
        return self.deleted_at is not None


class KnowledgeImage(models.Model):
    knowledge = models.ForeignKey(Knowledge, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='knowledge_images/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
