from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('district_admin', 'District Admin'),
        ('local_leader', 'Local Leader'),
        ('hospital', 'Hospital'),
        ('adopter', 'Adopter'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Add related_name to resolve conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')

class DistrictAdmin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='district_admin_profile')
    district_name = models.CharField(max_length=100)
    contact_info = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.district_name}"

class LocalLeader(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='local_leader_profile')
    district_admin = models.ForeignKey(DistrictAdmin, on_delete=models.CASCADE, related_name='local_leaders')
    village = models.CharField(max_length=100)
    cell = models.CharField(max_length=100)
    sector = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    contact_info = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.village}"

class Hospital(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='hospital_profile')
    local_leader = models.ForeignKey(LocalLeader, on_delete=models.CASCADE, related_name='hospitals')
    hospital_name = models.CharField(max_length=200)
    contact_info = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.hospital_name

class Adopter(models.Model):
    MARITAL_STATUS_CHOICES = (
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
    )
    
    EMPLOYMENT_STATUS_CHOICES = (
        ('employed', 'Employed'),
        ('unemployed', 'Unemployed'),
        ('self_employed', 'Self Employed'),
    )
    
    INCOME_LEVEL_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='adopter_profile')
    full_name = models.CharField(max_length=200)
    age = models.IntegerField()
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES)
    employment_status = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS_CHOICES)
    job_type = models.CharField(max_length=100, blank=True)
    income_level = models.CharField(max_length=20, choices=INCOME_LEVEL_CHOICES)
    address = models.TextField(blank=True)
    contact_info = models.TextField(blank=True)
    identification_number = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name
