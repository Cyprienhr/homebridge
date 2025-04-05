from django import forms
from .models import Child, AdoptionApplication
from accounts.models import Hospital

class ChildForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name'}))
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    gender = forms.ChoiceField(
        choices=Child.GENDER_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    abandonment_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    found_location_type = forms.ChoiceField(
        choices=Child.FOUND_LOCATION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    hospital = forms.ModelChoiceField(
        queryset=Hospital.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    village = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Village'}),
        required=False
    )
    cell = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cell'}),
        required=False
    )
    sector = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sector'}),
        required=False
    )
    district = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'District'}),
        required=False
    )
    status = forms.ChoiceField(
        choices=Child.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="'Available' means this child will be immediately visible for adoption. 'Pending' means the child's details will be reviewed first."
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Description', 'rows': 3}),
        required=False
    )
    photo = forms.ImageField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = Child
        fields = [
            'name', 'date_of_birth', 'gender', 'abandonment_date', 
            'found_location_type', 'hospital', 'village', 'cell', 
            'sector', 'district', 'status', 'description', 'photo'
        ]

    def __init__(self, *args, **kwargs):
        # Get user from kwargs if it exists
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter hospitals based on user type
        if user and user.user_type == 'local_leader':
            self.fields['hospital'].queryset = Hospital.objects.filter(local_leader__user=user)
            # Local leader can only create pending children
            self.fields['status'].choices = [
                ('pending', 'Pending')
            ]
            self.fields['status'].initial = 'pending'
            self.fields['status'].help_text = "As a Local Leader, reported children will be automatically set to 'Pending' for District Admin review."
        elif user and user.user_type == 'district_admin':
            # District admin can see all hospitals in their district
            self.fields['hospital'].queryset = Hospital.objects.filter(
                local_leader__district_admin__user=user
            )
            # Allow full status control
            self.fields['status'].initial = 'available'
            self.fields['status'].help_text = "As a District Admin, you can directly make children 'Available' for adoption."

    def clean(self):
        cleaned_data = super().clean()
        found_location_type = cleaned_data.get('found_location_type')
        hospital = cleaned_data.get('hospital')
        village = cleaned_data.get('village')
        cell = cleaned_data.get('cell')
        sector = cleaned_data.get('sector')
        district = cleaned_data.get('district')
        
        if found_location_type == 'hospital' and not hospital:
            self.add_error('hospital', 'Please select a hospital where the child was found.')
        
        if found_location_type == 'street':
            if not village:
                self.add_error('village', 'Please enter the village where the child was found.')
            if not cell:
                self.add_error('cell', 'Please enter the cell where the child was found.')
            if not sector:
                self.add_error('sector', 'Please enter the sector where the child was found.')
            if not district:
                self.add_error('district', 'Please enter the district where the child was found.')
        
        return cleaned_data

class AdoptionApplicationForm(forms.ModelForm):
    class Meta:
        model = AdoptionApplication
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Any additional information you would like to provide', 'rows': 3}),
        }

class AdoptionApplicationUpdateForm(forms.ModelForm):
    application_status = forms.ChoiceField(
        choices=AdoptionApplication.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    meeting_appointment = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        required=False
    )
    meeting_status = forms.ChoiceField(
        choices=AdoptionApplication.MEETING_STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Notes', 'rows': 3}),
        required=False
    )

    class Meta:
        model = AdoptionApplication
        fields = ['application_status', 'meeting_appointment', 'meeting_status', 'notes']
