from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm, PasswordChangeForm
from django.core.exceptions import ValidationError
from .models import User, DistrictAdmin, LocalLeader, Hospital, Adopter

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'user_type', 'phone_number', 'address')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Disable password validation
        self.fields['password1'].help_text = ""
        self.fields['password2'].help_text = ""
        # Add show password toggle
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'data-toggle': 'password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'data-toggle': 'password'})

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'phone_number', 'address')

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 
        'placeholder': 'Password', 
        'id': 'password-field',
        'data-toggle': 'password'
    }))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_messages['invalid_login'] = 'Please enter correct username and password.'

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}))
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Password', 
            'id': 'password-field1',
            'data-toggle': 'password'
        }),
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Confirm Password', 
            'id': 'password-field2',
            'data-toggle': 'password'
        }),
    )
    phone_number = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}), required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Address', 'rows': 3}), required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'phone_number', 'address')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already exists")
        return email

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove password validation
        self.fields['password1'].help_text = ""
        self.fields['password2'].help_text = ""
        
    # Override the password validation methods to allow any password
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("The two password fields didn't match.")
        return password2
    
    def _post_clean(self):
        super(UserCreationForm, self)._post_clean()
        # Skip the password validation
        if 'password1' in self.cleaned_data:
            try:
                pass
            except ValidationError as error:
                self.add_error('password2', error)

class DistrictAdminForm(forms.ModelForm):
    class Meta:
        model = DistrictAdmin
        fields = ('district_name', 'contact_info')

class LocalLeaderForm(forms.ModelForm):
    village = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Village'}))
    cell = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cell'}))
    sector = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sector'}))
    district = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'District'}))
    contact_info = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Contact Information', 'rows': 3}))

    class Meta:
        model = LocalLeader
        fields = ('village', 'cell', 'sector', 'district', 'contact_info')

class HospitalForm(forms.ModelForm):
    hospital_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Hospital Name'}))
    contact_info = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Contact Information', 'rows': 3}))
    local_leader = forms.ModelChoiceField(
        queryset=LocalLeader.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        empty_label="Select a Local Leader"
    )

    class Meta:
        model = Hospital
        fields = ('hospital_name', 'contact_info', 'local_leader')
        
    def __init__(self, *args, **kwargs):
        district_admin = kwargs.pop('district_admin', None)
        local_leader_user = kwargs.pop('local_leader_user', None)
        super().__init__(*args, **kwargs)
        
        if district_admin:
            # Filter local leaders by district admin
            self.fields['local_leader'].queryset = LocalLeader.objects.filter(district_admin=district_admin)
        
        # If this form is being used by a local leader, hide the local_leader field
        # as it will be automatically set to the local leader in the view
        if local_leader_user:
            self.fields['local_leader'].required = False
            self.fields['local_leader'].widget = forms.HiddenInput()

class AdopterForm(forms.ModelForm):
    address = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Address', 'rows': 3}))
    contact_info = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Contact Information', 'rows': 3}))
    identification_number = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Identification Number'}))
    
    class Meta:
        model = Adopter
        fields = ('full_name', 'age', 'marital_status', 'employment_status', 'job_type', 'income_level', 'address', 'contact_info', 'identification_number')

class AdopterRegistrationForm(forms.ModelForm):
    MARITAL_STATUS_CHOICES = Adopter.MARITAL_STATUS_CHOICES
    EMPLOYMENT_STATUS_CHOICES = Adopter.EMPLOYMENT_STATUS_CHOICES
    INCOME_LEVEL_CHOICES = Adopter.INCOME_LEVEL_CHOICES
    
    full_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}))
    age = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Age'}))
    marital_status = forms.ChoiceField(choices=MARITAL_STATUS_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    employment_status = forms.ChoiceField(choices=EMPLOYMENT_STATUS_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    job_type = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Job Type'}), required=False)
    income_level = forms.ChoiceField(choices=INCOME_LEVEL_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = Adopter
        fields = ('full_name', 'age', 'marital_status', 'employment_status', 'job_type', 'income_level')

class UserProfileForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}), required=False)
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}), required=False)
    phone_number = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}), required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Address', 'rows': 3}), required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'address')

class PasswordChangeCustomForm(PasswordChangeForm):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 
        'placeholder': 'Current Password', 
        'id': 'current-password-field',
        'data-toggle': 'password'
    }))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 
        'placeholder': 'New Password', 
        'id': 'new-password-field1',
        'data-toggle': 'password'
    }))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 
        'placeholder': 'Confirm New Password', 
        'id': 'new-password-field2',
        'data-toggle': 'password'
    }))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Override the default password validation messages
        self.fields['new_password1'].help_text = ""
        self.fields['new_password2'].help_text = ""
    
    # Override the password validation methods to allow any password
    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                raise ValidationError("The two password fields didn't match.")
        return password2
    
    def _post_clean(self):
        super(PasswordChangeForm, self)._post_clean()
        # Skip the password validation
        password = self.cleaned_data.get('new_password1')
        if password:
            try:
                pass
            except ValidationError as error:
                self.add_error('new_password2', error)
