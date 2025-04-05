from django.db import models
from accounts.models import User, Hospital, LocalLeader

class Child(models.Model):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('unknown', 'Unknown'),
    )
    
    FOUND_LOCATION_CHOICES = (
        ('hospital', 'Hospital'),
        ('street', 'Street'),
    )
    
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('pending', 'Pending'),
        ('adopted', 'Adopted'),
    )

    name = models.CharField(max_length=200)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    abandonment_date = models.DateField()
    found_location_type = models.CharField(max_length=20, choices=FOUND_LOCATION_CHOICES)
    hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reported_children')
    
    # Location details if found on street
    village = models.CharField(max_length=100, blank=True)
    cell = models.CharField(max_length=100, blank=True)
    sector = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    description = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True, help_text="Notes from district admin review")
    photo = models.ImageField(upload_to='child_photos/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.status}"

class AdoptionApplication(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    MEETING_STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('canceled', 'Canceled'),
        ('completed', 'Completed'),
    )

    adopter = models.ForeignKey('accounts.Adopter', on_delete=models.CASCADE, related_name='applications')
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='applications')
    application_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    application_date = models.DateTimeField(auto_now_add=True)
    meeting_appointment = models.DateTimeField(null=True, blank=True)
    meeting_status = models.CharField(max_length=20, choices=MEETING_STATUS_CHOICES, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['adopter', 'child']

    def __str__(self):
        return f"{self.adopter.full_name} - {self.child.name} - {self.application_status}"
