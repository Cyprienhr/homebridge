from django.db import models
from accounts.models import User, Adopter
from children.models import Child, AdoptionApplication

class Appointment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    district_admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    adopter = models.ForeignKey(Adopter, on_delete=models.CASCADE, related_name='appointments')
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='appointments')
    application = models.ForeignKey(AdoptionApplication, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['appointment_date']

    def __str__(self):
        return f"Meeting with {self.adopter.full_name} for {self.child.name}"
