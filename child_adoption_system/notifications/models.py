from django.db import models
from accounts.models import User
from children.models import Child, AdoptionApplication

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='received_notifications', null=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications', null=True, blank=True)
    title = models.CharField(max_length=100, default="System Notification")
    message = models.TextField(default="")
    read = models.BooleanField(default=False)
    related_link = models.CharField(max_length=255, blank=True)  # URL to related resource
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.recipient.username}"
    
    def mark_as_read(self):
        self.read = True
        self.save()
