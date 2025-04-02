from django import forms
from .models import Appointment
from accounts.models import Adopter
from children.models import Child, AdoptionApplication

class AppointmentForm(forms.ModelForm):
    appointment_date = forms.DateTimeField(
        input_formats=['%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M', '%Y-%m-%d'],
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'text',  # Changed from datetime-local to text for flatpickr compatibility
            'autocomplete': 'off'
        })
    )
    status = forms.ChoiceField(
        choices=Appointment.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Notes', 'rows': 3}),
        required=False
    )
    adopter = forms.ModelChoiceField(
        queryset=Adopter.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    child = forms.ModelChoiceField(
        queryset=Child.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    application = forms.ModelChoiceField(
        queryset=AdoptionApplication.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Appointment
        fields = ['adopter', 'child', 'application', 'appointment_date', 'status', 'notes']
    
    def __init__(self, *args, **kwargs):
        application_id = kwargs.pop('application_id', None)
        super().__init__(*args, **kwargs)
        
        if application_id:
            application = AdoptionApplication.objects.get(id=application_id)
            self.fields['adopter'].initial = application.adopter
            self.fields['adopter'].widget.attrs['readonly'] = True
            self.fields['child'].initial = application.child
            self.fields['child'].widget.attrs['readonly'] = True
            self.fields['application'].initial = application
            self.fields['application'].widget.attrs['readonly'] = True
            
            # Limit application choices to the specific application
            self.fields['application'].queryset = AdoptionApplication.objects.filter(id=application_id)
            self.fields['adopter'].queryset = Adopter.objects.filter(id=application.adopter.id)
            self.fields['child'].queryset = Child.objects.filter(id=application.child.id)
        else:
            # Only show applications that have a status of 'pending'
            pending_applications = AdoptionApplication.objects.filter(application_status='pending')
            self.fields['application'].queryset = pending_applications
            
            # Get children and adopters from pending applications
            child_ids = pending_applications.values_list('child_id', flat=True)
            adopter_ids = pending_applications.values_list('adopter_id', flat=True)
            
            self.fields['child'].queryset = Child.objects.filter(id__in=child_ids)
            self.fields['adopter'].queryset = Adopter.objects.filter(id__in=adopter_ids)
    
    def clean(self):
        cleaned_data = super().clean()
        adopter = cleaned_data.get('adopter')
        child = cleaned_data.get('child')
        application = cleaned_data.get('application')
        
        # Ensure the selected application matches the adopter and child
        if application and (application.adopter != adopter or application.child != child):
            self.add_error('application', 'The selected application does not match the selected adopter and child.')
        
        return cleaned_data

class AppointmentUpdateForm(forms.ModelForm):
    appointment_date = forms.DateTimeField(
        input_formats=['%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M', '%Y-%m-%d'],
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'text',  # Changed from datetime-local to text for flatpickr compatibility
            'autocomplete': 'off'
        })
    )
    status = forms.ChoiceField(
        choices=Appointment.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Notes', 'rows': 3}),
        required=False
    )

    class Meta:
        model = Appointment
        fields = ['appointment_date', 'status', 'notes']
