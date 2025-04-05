from django.db import models
from accounts.models import User

# Create your models here.

class AuditLog(models.Model):
    ACTION_CHOICES = (
        ('delete', 'Delete'),
        ('update', 'Update'),
        ('create', 'Create'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_id = models.IntegerField()
    object_repr = models.CharField(max_length=200)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action} - {self.model_name} - {self.object_repr}"
