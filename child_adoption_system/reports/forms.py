from django import forms
from .models import Report
from children.models import Child
from django.db import models
from django.utils import timezone

class ReportForm(forms.ModelForm):
    child = forms.ModelChoiceField(
        queryset=Child.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    report_details = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Details of the report', 'rows': 5})
    )

    class Meta:
        model = Report
        fields = ['child', 'report_details']
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter children based on user type
        if user:
            if user.user_type == 'hospital':
                # Hospital can report children they have reported
                self.fields['child'].queryset = Child.objects.filter(hospital__user=user)
            elif user.user_type == 'local_leader':
                # Local leader can report children in their area
                self.fields['child'].queryset = Child.objects.filter(
                    models.Q(sector=user.local_leader_profile.sector) | 
                    models.Q(hospital__local_leader__user=user)
                )


class AbandonedChildReportForm(forms.Form):
    # Child Information
    name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Child name or placeholder if unknown'})
    )
    
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=False,
        help_text="If exact date is unknown, provide an estimate"
    )
    
    GENDER_CHOICES = Child.GENDER_CHOICES
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    abandonment_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        initial=timezone.now().date(),
        help_text="When was the child found or abandoned"
    )
    
    LOCATION_CHOICES = Child.FOUND_LOCATION_CHOICES
    found_location_type = forms.ChoiceField(
        choices=LOCATION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Where was the child found?"
    )
    
    # Location details if found on street
    village = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False,
        help_text="Required if found on street"
    )
    
    cell = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False,
        help_text="Required if found on street"
    )
    
    sector = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False,
        help_text="Required if found on street"
    )
    
    district = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False,
        help_text="Required if found on street"
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False,
        help_text="Physical appearance, clothes worn, etc."
    )
    
    photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    # Report details
    report_details = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        label="Report Details",
        help_text="Please provide detailed information about the circumstances in which the child was found/abandoned"
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        found_location = cleaned_data.get('found_location_type')
        
        # If found on street, location details are required
        if found_location == 'street':
            for field in ['village', 'cell', 'sector', 'district']:
                if not cleaned_data.get(field):
                    self.add_error(field, f"{field.capitalize()} is required when found on street")
        
        return cleaned_data
    
    def save(self):
        """Create both Child and Report objects"""
        data = self.cleaned_data
        
        # Create Child
        child = Child(
            name=data['name'],
            date_of_birth=data.get('date_of_birth') or timezone.now().date(),
            gender=data['gender'],
            abandonment_date=data['abandonment_date'],
            found_location_type=data['found_location_type'],
            reported_by=self.user,
            village=data.get('village', ''),
            cell=data.get('cell', ''),
            sector=data.get('sector', ''),
            district=data.get('district', ''),
            description=data.get('description', ''),
            photo=data.get('photo'),
            status='pending'  # Set status to pending instead of available
        )
        
        # If hospital user, set hospital
        if self.user.user_type == 'hospital':
            from accounts.models import Hospital
            hospital = Hospital.objects.get(user=self.user)
            child.hospital = hospital
        
        child.save()
        
        # Create Report
        report = Report(
            reported_by=self.user,
            child=child,
            report_details=data['report_details'],
            status='pending'  # Ensure report status is also pending
        )
        report.save()
        
        return report


class ReportUpdateForm(forms.Form):
    """Simple form for report status update with no validation logic"""
    STATUS_CHOICES = Report.REPORT_STATUS_CHOICES
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Report Status"
    )
    
    district_admin_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Notes from the district admin',
            'rows': 5
        }),
        required=False,
        label="District Admin Notes"
    )
    
    def __init__(self, *args, **kwargs):
        # Extract instance but don't pass it to parent
        instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)
        
        # If there's an instance, set initial values
        if instance:
            self.fields['status'].initial = instance.status
            self.fields['district_admin_notes'].initial = instance.district_admin_notes


class ChildAdoptionApprovalForm(forms.Form):
    """Simple form for child adoption approval with no validation logic"""
    STATUS_CHOICES = (
        ('pending', 'Keep Pending (Not Visible to Adopters)'),
        ('available', 'Make Available for Adoption (Visible to Adopters)'),
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control form-control-lg'}),
        label="Adoption Status",
        help_text="Select 'Make Available for Adoption' to make this child visible to potential adopters. This will also mark the report as resolved."
    )
    
    admin_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Provide detailed information about why this child should be made available for adoption...'
        }),
        required=False,
        label="Admin Notes",
        help_text="REQUIRED: Add detailed notes regarding the approval decision, circumstances of the child, and any relevant information for the adoption process."
    )
    
    def __init__(self, *args, **kwargs):
        # Extract instance but don't pass it to parent
        instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)
        
        # If there's an instance, set initial values
        if instance:
            self.fields['status'].initial = instance.status
            self.fields['admin_notes'].initial = instance.admin_notes
