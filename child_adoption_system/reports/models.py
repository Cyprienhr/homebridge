from django.db import models
from accounts.models import User
from children.models import Child

class Report(models.Model):
    REPORT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('resolved', 'Resolved'),
    )

    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='reports')
    report_date = models.DateTimeField(auto_now_add=True)
    report_details = models.TextField()
    status = models.CharField(max_length=20, choices=REPORT_STATUS_CHOICES, default='pending')
    district_admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Report for {self.child.name} by {self.reported_by.username}"
