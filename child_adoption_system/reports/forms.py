from django import forms
from .models import Report
from children.models import Child
from django.db import models

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

class ReportUpdateForm(forms.ModelForm):
    STATUS_CHOICES = Report.REPORT_STATUS_CHOICES
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    district_admin_notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Notes from the district admin', 'rows': 5}),
        required=False
    )

    class Meta:
        model = Report
        fields = ['status', 'district_admin_notes']
