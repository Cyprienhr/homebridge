from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.db import transaction
from .forms import (
    CustomUserCreationForm, AdopterRegistrationForm, DistrictAdminForm,
    LocalLeaderForm, HospitalForm, AdopterForm,
    UserRegistrationForm, CustomAuthenticationForm, UserProfileForm,
    PasswordChangeCustomForm
)
from .models import User, DistrictAdmin, LocalLeader, Hospital, Adopter
from audit.models import AuditLog

# Create your views here.

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

class CustomLogoutView(LogoutView):
    next_page = 'home'

class AdopterRegistrationView(CreateView):
    form_class = AdopterRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.save()
        login(self.request, user)
        return response

@login_required
def profile(request):
    user = request.user
    context = {'user': user}
    
    # Add user-specific profile to context
    if user.user_type == 'district_admin':
        district_admin = DistrictAdmin.objects.get(user=user)
        context['district_admin'] = district_admin
    elif user.user_type == 'local_leader':
        local_leader = LocalLeader.objects.get(user=user)
        context['local_leader'] = local_leader
    elif user.user_type == 'hospital':
        hospital = Hospital.objects.get(user=user)
        context['hospital'] = hospital
    elif user.user_type == 'adopter':
        adopter = Adopter.objects.get(user=user)
        context['adopter'] = adopter
    
    if request.method == 'POST':
        # Handle form submissions
        form = UserProfileForm(request.POST, instance=request.user)
        
        # Additional form based on user type
        if user.user_type == 'district_admin':
            district_admin_form = DistrictAdminForm(request.POST, instance=district_admin)
            context['district_admin_form'] = district_admin_form
            if form.is_valid() and district_admin_form.is_valid():
                with transaction.atomic():
                    form.save()
                    district_admin_form.save()
                    AuditLog.objects.create(
                        user=user,
                        action='update',
                        model_name='User',
                        object_id=user.id,
                        object_repr=f'User {user.username}',
                        reason=f'User updated profile'
                    )
                messages.success(request, 'Your profile has been updated successfully.')
                return redirect('accounts:profile')
        
        elif user.user_type == 'local_leader':
            local_leader_form = LocalLeaderForm(request.POST, instance=local_leader)
            context['local_leader_form'] = local_leader_form
            if form.is_valid() and local_leader_form.is_valid():
                with transaction.atomic():
                    form.save()
                    local_leader_form.save()
                    AuditLog.objects.create(
                        user=user,
                        action='update',
                        model_name='User',
                        object_id=user.id,
                        object_repr=f'User {user.username}',
                        reason=f'User updated profile'
                    )
                messages.success(request, 'Your profile has been updated successfully.')
                return redirect('accounts:profile')
        
        elif user.user_type == 'hospital':
            hospital_form = HospitalForm(request.POST, instance=hospital)
            context['hospital_form'] = hospital_form
            if form.is_valid() and hospital_form.is_valid():
                with transaction.atomic():
                    form.save()
                    hospital_form.save()
                    AuditLog.objects.create(
                        user=user,
                        action='update',
                        model_name='User',
                        object_id=user.id,
                        object_repr=f'User {user.username}',
                        reason=f'User updated profile'
                    )
                messages.success(request, 'Your profile has been updated successfully.')
                return redirect('accounts:profile')
        
        elif user.user_type == 'adopter':
            adopter_form = AdopterForm(request.POST, instance=adopter)
            context['adopter_form'] = adopter_form
            if form.is_valid() and adopter_form.is_valid():
                with transaction.atomic():
                    form.save()
                    adopter_form.save()
                    AuditLog.objects.create(
                        user=user,
                        action='update',
                        model_name='User',
                        object_id=user.id,
                        object_repr=f'User {user.username}',
                        reason=f'User updated profile'
                    )
                messages.success(request, 'Your profile has been updated successfully.')
                return redirect('accounts:profile')
        
        context['form'] = form
        messages.error(request, 'Please correct the errors below.')
    else:
        # Prepare empty forms
        form = UserProfileForm(instance=request.user)
        context['form'] = form
        
        # Add additional form based on user type
        if user.user_type == 'district_admin':
            context['district_admin_form'] = DistrictAdminForm(instance=district_admin)
        elif user.user_type == 'local_leader':
            context['local_leader_form'] = LocalLeaderForm(instance=local_leader)
        elif user.user_type == 'hospital':
            context['hospital_form'] = HospitalForm(instance=hospital)
        elif user.user_type == 'adopter':
            context['adopter_form'] = AdopterForm(instance=adopter)
    
    return render(request, 'accounts/profile.html', context)

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeCustomForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Stay logged in after password change
            update_session_auth_hash(request, user)
            # Create audit log
            AuditLog.objects.create(
                user=request.user,
                action='update',
                model_name='User',
                object_id=request.user.id,
                object_repr=f'User {request.user.username}',
                reason='Password changed'
            )
            messages.success(request, 'Your password has been changed successfully.')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeCustomForm(request.user)
    
    return render(request, 'accounts/password_change.html', {'form': form})

def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        adopter_form = AdopterRegistrationForm(request.POST)
        
        if user_form.is_valid() and adopter_form.is_valid():
            with transaction.atomic():
                user = user_form.save(commit=False)
                user.user_type = 'adopter'
                user.save()
                
                adopter = adopter_form.save(commit=False)
                adopter.user = user
                adopter.save()
                
                # Create audit log
                AuditLog.objects.create(
                    user=user,
                    action='create',
                    model_name='User',
                    object_id=user.id,
                    object_repr=f'User {user.username}',
                    reason=f'User registered as an adopter'
                )
                
                # Log the user in
                login(request, user)
                messages.success(request, 'Registration successful!')
                return redirect('dashboard:adopter_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserRegistrationForm()
        adopter_form = AdopterRegistrationForm()
    
    return render(request, 'accounts/register.html', {
        'user_form': user_form,
        'adopter_form': adopter_form
    })

def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                # Create audit log
                AuditLog.objects.create(
                    user=user,
                    action='create',
                    model_name='Session',
                    object_id=user.id,
                    object_repr=f'User {user.username}',
                    reason=f'User logged in'
                )
                
                # Redirect based on user type
                if user.user_type == 'district_admin':
                    return redirect('dashboard:admin_dashboard')
                elif user.user_type == 'local_leader':
                    return redirect('dashboard:local_leader_dashboard')
                elif user.user_type == 'hospital':
                    return redirect('dashboard:hospital_dashboard')
                else:  # adopter
                    return redirect('dashboard:adopter_dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def user_logout(request):
    if request.user.is_authenticated:
        # Create audit log
        AuditLog.objects.create(
            user=request.user,
            action='delete',
            model_name='Session',
            object_id=request.user.id,
            object_repr=f'User {request.user.username}',
            reason=f'User logged out'
        )
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

@login_required
def create_local_leader(request):
    # Only district admin can create local leaders
    if request.user.user_type != 'district_admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        local_leader_form = LocalLeaderForm(request.POST)
        
        if user_form.is_valid() and local_leader_form.is_valid():
            with transaction.atomic():
                user = user_form.save(commit=False)
                user.user_type = 'local_leader'
                user.save()
                
                district_admin = DistrictAdmin.objects.get(user=request.user)
                local_leader = local_leader_form.save(commit=False)
                local_leader.user = user
                local_leader.district_admin = district_admin
                local_leader.save()
                
                # Create audit log
                AuditLog.objects.create(
                    user=request.user,
                    action='create',
                    model_name='LocalLeader',
                    object_id=local_leader.id,
                    object_repr=f'Local Leader {user.username}',
                    reason=f'Created by District Admin {request.user.username}'
                )
                
                messages.success(request, 'Local Leader account created successfully!')
                return redirect('accounts:local_leader_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserRegistrationForm()
        local_leader_form = LocalLeaderForm()
    
    return render(request, 'accounts/create_local_leader.html', {
        'user_form': user_form,
        'local_leader_form': local_leader_form
    })

@login_required
def local_leader_list(request):
    # Only district admin can view local leaders
    if request.user.user_type != 'district_admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:dashboard')
    
    district_admin = DistrictAdmin.objects.get(user=request.user)
    local_leaders = LocalLeader.objects.filter(district_admin=district_admin)
    
    return render(request, 'accounts/local_leader_list.html', {'local_leaders': local_leaders})

@login_required
def delete_local_leader(request, pk):
    # Only district admin can delete local leaders
    if request.user.user_type != 'district_admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:dashboard')
    
    local_leader = get_object_or_404(LocalLeader, pk=pk)
    district_admin = DistrictAdmin.objects.get(user=request.user)
    
    # Ensure the local leader belongs to this district admin
    if local_leader.district_admin != district_admin:
        messages.error(request, 'You do not have permission to delete this local leader.')
        return redirect('accounts:local_leader_list')
    
    user = local_leader.user
    username = user.username
    
    if request.method == 'POST':
        # Create audit log before deletion
        AuditLog.objects.create(
            user=request.user,
            action='delete',
            model_name='LocalLeader',
            object_id=local_leader.id,
            object_repr=f'Local Leader {username}',
            reason=f'Deleted by District Admin {request.user.username}'
        )
        
        user.delete()  # This will cascade delete the LocalLeader due to OneToOne relation
        messages.success(request, f'Local Leader {username} has been deleted successfully.')
        return redirect('accounts:local_leader_list')
    
    return render(request, 'accounts/delete_local_leader.html', {'local_leader': local_leader})

@login_required
def create_hospital(request):
    # Only district admin or local leader can create hospitals
    if request.user.user_type not in ['district_admin', 'local_leader']:
        messages.error(request, 'You do not have permission to create hospitals.')
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        
        # Initialize hospital form with appropriate parameters based on user type
        if request.user.user_type == 'district_admin':
            district_admin = DistrictAdmin.objects.get(user=request.user)
            hospital_form = HospitalForm(request.POST, district_admin=district_admin)
        else:  # local_leader
            hospital_form = HospitalForm(request.POST, local_leader_user=request.user)
        
        if user_form.is_valid() and hospital_form.is_valid():
            try:
                with transaction.atomic():
                    user = user_form.save(commit=False)
                    user.user_type = 'hospital'
                    user.save()
                    
                    hospital = hospital_form.save(commit=False)
                    hospital.user = user
                    
                    if request.user.user_type == 'local_leader':
                        local_leader = LocalLeader.objects.get(user=request.user)
                        hospital.local_leader = local_leader
                    # District admin selects local leader through the form
                    
                    hospital.save()
                    
                    # Create audit log
                    AuditLog.objects.create(
                        user=request.user,
                        action='create',
                        model_name='Hospital',
                        object_id=hospital.id,
                        object_repr=f'Hospital {user.username}',
                        reason=f'Created by {request.user.get_user_type_display()} {request.user.username}'
                    )
                    
                    messages.success(request, 'Hospital account created successfully!')
                    return redirect('accounts:hospital_list')
            except Exception as e:
                messages.error(request, f'Error creating hospital: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserRegistrationForm()
        
        # Initialize hospital form with appropriate parameters based on user type
        if request.user.user_type == 'district_admin':
            try:
                district_admin = DistrictAdmin.objects.get(user=request.user)
                hospital_form = HospitalForm(district_admin=district_admin)
            except DistrictAdmin.DoesNotExist:
                messages.error(request, 'District Admin profile not found.')
                hospital_form = HospitalForm()
        else:  # local_leader
            hospital_form = HospitalForm(local_leader_user=request.user)
    
    context = {
        'user_form': user_form,
        'hospital_form': hospital_form
    }
    
    # If district admin, check if local leaders exist
    if request.user.user_type == 'district_admin':
        try:
            district_admin = DistrictAdmin.objects.get(user=request.user)
            local_leaders = LocalLeader.objects.filter(district_admin=district_admin)
            
            # Add debug info about local leaders
            if not local_leaders.exists():
                messages.warning(request, 'You do not have any Local Leaders in your district. Please create at least one Local Leader first.')
                return redirect('accounts:local_leader_list')
        except DistrictAdmin.DoesNotExist:
            messages.error(request, 'District Admin profile not found.')
    
    return render(request, 'accounts/create_hospital.html', context)

@login_required
def hospital_list(request):
    # Only district admin or local leader can view hospitals
    if request.user.user_type not in ['district_admin', 'local_leader']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:dashboard')
    
    context = {}
    
    if request.user.user_type == 'district_admin':
        district_admin = DistrictAdmin.objects.get(user=request.user)
        local_leaders = LocalLeader.objects.filter(district_admin=district_admin)
        hospitals = Hospital.objects.filter(local_leader__in=local_leaders)
        
        # Check if local leaders exist
        context['local_leaders_exist'] = local_leaders.exists()
    else:  # local_leader
        local_leader = LocalLeader.objects.get(user=request.user)
        hospitals = Hospital.objects.filter(local_leader=local_leader)
        context['local_leaders_exist'] = True  # Local leaders don't need this check
    
    context['hospitals'] = hospitals
    return render(request, 'accounts/hospital_list.html', context)

@login_required
def delete_hospital(request, pk):
    # Only district admin or local leader can delete hospitals
    if request.user.user_type not in ['district_admin', 'local_leader']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:dashboard')
    
    hospital = get_object_or_404(Hospital, pk=pk)
    
    # Ensure the hospital belongs to this local leader or district
    if request.user.user_type == 'local_leader':
        local_leader = LocalLeader.objects.get(user=request.user)
        if hospital.local_leader != local_leader:
            messages.error(request, 'You do not have permission to delete this hospital.')
            return redirect('accounts:hospital_list')
    else:  # district_admin
        district_admin = DistrictAdmin.objects.get(user=request.user)
        if hospital.local_leader.district_admin != district_admin:
            messages.error(request, 'You do not have permission to delete this hospital.')
            return redirect('accounts:hospital_list')
    
    user = hospital.user
    username = user.username
    
    if request.method == 'POST':
        # Create audit log before deletion
        AuditLog.objects.create(
            user=request.user,
            action='delete',
            model_name='Hospital',
            object_id=hospital.id,
            object_repr=f'Hospital {username}',
            reason=f'Deleted by {request.user.get_user_type_display()} {request.user.username}'
        )
        
        user.delete()  # This will cascade delete the Hospital due to OneToOne relation
        messages.success(request, f'Hospital {username} has been deleted successfully.')
        return redirect('accounts:hospital_list')
    
    return render(request, 'accounts/delete_hospital.html', {'hospital': hospital})

@login_required
def adopter_list(request):
    # Only district admin can view all adopters
    if request.user.user_type != 'district_admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:dashboard')
    
    adopters = Adopter.objects.all()
    return render(request, 'accounts/adopter_list.html', {'adopters': adopters})

@login_required
def edit_adopter(request, pk):
    # Only district admin can edit adopters
    if request.user.user_type != 'district_admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:dashboard')
    
    adopter = get_object_or_404(Adopter, pk=pk)
    
    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, instance=adopter.user)
        adopter_form = AdopterForm(request.POST, instance=adopter)
        
        if user_form.is_valid() and adopter_form.is_valid():
            with transaction.atomic():
                user = user_form.save()
                adopter = adopter_form.save()
                
                # Create audit log
                AuditLog.objects.create(
                    user=request.user,
                    action='update',
                    model_name='Adopter',
                    object_id=adopter.id,
                    object_repr=f'Adopter {adopter.full_name}',
                    reason=f'Updated by District Admin {request.user.username}'
                )
                
                messages.success(request, 'Adopter account updated successfully!')
                return redirect('accounts:adopter_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserProfileForm(instance=adopter.user)
        adopter_form = AdopterForm(instance=adopter)
    
    return render(request, 'accounts/edit_adopter.html', {
        'user_form': user_form,
        'adopter_form': adopter_form,
        'adopter': adopter
    })

@login_required
def delete_adopter(request, pk):
    # Only district admin can delete adopters
    if request.user.user_type != 'district_admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:dashboard')
    
    adopter = get_object_or_404(Adopter, pk=pk)
    user = adopter.user
    full_name = adopter.full_name
    
    if request.method == 'POST':
        # Create audit log before deletion
        AuditLog.objects.create(
            user=request.user,
            action='delete',
            model_name='Adopter',
            object_id=adopter.id,
            object_repr=f'Adopter {full_name}',
            reason=f'Deleted by District Admin {request.user.username}'
        )
        
        user.delete()  # This will cascade delete the Adopter due to OneToOne relation
        messages.success(request, f'Adopter {full_name} has been deleted successfully.')
        return redirect('accounts:adopter_list')
    
    return render(request, 'accounts/delete_adopter.html', {'adopter': adopter})

def initialize_admin(request):
    """
    Initialize the default admin account if it doesn't exist.
    This view is mainly for setup purposes.
    """
    if User.objects.filter(username='Nyarugenge').exists():
        messages.info(request, 'Default admin account already exists.')
        return redirect('login')
    
    # Create the default admin account
    with transaction.atomic():
        admin_user = User.objects.create_user(
            username='Nyarugenge',
            email='hrcyprien@gmail.com',
            password='rwendere',
            user_type='district_admin', 
            first_name='Nyarugenge',
            last_name='District'
        )
        
        district_admin = DistrictAdmin.objects.create(
            user=admin_user,
            district_name='Nyarugenge',
            contact_info='Nyarugenge District Office\nPhone: +250 788 123 456\nEmail: hrcyprien@gmail.com'
        )
        
        # Create audit log
        AuditLog.objects.create(
            user=admin_user,
            action='create',
            model_name='DistrictAdmin',
            object_id=district_admin.id,
            object_repr='Default District Admin',
            reason='System initialization'
        )
    
    messages.success(request, 'Default admin account created successfully!')
    return redirect('login')

@login_required
def edit_local_leader(request, pk):
    # Only district admin can edit local leaders
    if request.user.user_type != 'district_admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard:dashboard')
    
    local_leader = get_object_or_404(LocalLeader, pk=pk)
    district_admin = DistrictAdmin.objects.get(user=request.user)
    
    # Ensure the local leader belongs to this district admin
    if local_leader.district_admin != district_admin:
        messages.error(request, 'You do not have permission to edit this local leader.')
        return redirect('accounts:local_leader_list')
    
    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, instance=local_leader.user)
        local_leader_form = LocalLeaderForm(request.POST, instance=local_leader)
        
        if user_form.is_valid() and local_leader_form.is_valid():
            with transaction.atomic():
                user = user_form.save()
                local_leader = local_leader_form.save()
                
                # Create audit log
                AuditLog.objects.create(
                    user=request.user,
                    action='update',
                    model_name='LocalLeader',
                    object_id=local_leader.id,
                    object_repr=f'Local Leader {user.username}',
                    reason=f'Updated by District Admin {request.user.username}'
                )
                
                messages.success(request, 'Local Leader account updated successfully!')
                return redirect('accounts:local_leader_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserProfileForm(instance=local_leader.user)
        local_leader_form = LocalLeaderForm(instance=local_leader)
    
    return render(request, 'accounts/edit_local_leader.html', {
        'user_form': user_form,
        'local_leader_form': local_leader_form,
        'local_leader': local_leader
    })

@login_required
def edit_hospital(request, pk):
    # Only district admin or local leader can edit hospitals
    if request.user.user_type not in ['district_admin', 'local_leader']:
        messages.error(request, 'You do not have permission to edit hospitals.')
        return redirect('dashboard:dashboard')
    
    try:
        # Determine if the user has permission to edit this hospital
        if request.user.user_type == 'local_leader':
            local_leader = LocalLeader.objects.get(user=request.user)
            hospital = get_object_or_404(Hospital, id=pk, local_leader=local_leader)
        else:  # district_admin
            district_admin = DistrictAdmin.objects.get(user=request.user)
            hospital = get_object_or_404(Hospital, id=pk, local_leader__district_admin=district_admin)
    except (LocalLeader.DoesNotExist, DistrictAdmin.DoesNotExist):
        messages.error(request, 'Your profile is not properly set up.')
        return redirect('dashboard:dashboard')
    except Hospital.DoesNotExist:
        messages.error(request, 'Hospital not found or you do not have permission to edit it.')
        return redirect('accounts:hospital_list')
    
    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, instance=hospital.user)
        
        # Initialize hospital form with appropriate parameters
        if request.user.user_type == 'district_admin':
            district_admin = DistrictAdmin.objects.get(user=request.user)
            hospital_form = HospitalForm(request.POST, instance=hospital, district_admin=district_admin)
        else:  # local_leader
            hospital_form = HospitalForm(request.POST, instance=hospital, local_leader_user=request.user)
        
        if user_form.is_valid() and hospital_form.is_valid():
            with transaction.atomic():
                user = user_form.save()
                
                # If local leader is editing, ensure we don't change the local_leader field
                if request.user.user_type == 'local_leader':
                    hospital = hospital_form.save(commit=False)
                    local_leader = LocalLeader.objects.get(user=request.user)
                    hospital.local_leader = local_leader
                    hospital.save()
                else:
                    hospital = hospital_form.save()
                
                # Create audit log
                AuditLog.objects.create(
                    user=request.user,
                    action='update',
                    model_name='Hospital',
                    object_id=hospital.id,
                    object_repr=f'Hospital {user.username}',
                    reason=f'Updated by {request.user.get_user_type_display()} {request.user.username}'
                )
                
                messages.success(request, 'Hospital account updated successfully!')
                return redirect('accounts:hospital_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserProfileForm(instance=hospital.user)
        
        # Initialize hospital form with appropriate parameters
        if request.user.user_type == 'district_admin':
            district_admin = DistrictAdmin.objects.get(user=request.user)
            hospital_form = HospitalForm(instance=hospital, district_admin=district_admin)
        else:  # local_leader
            hospital_form = HospitalForm(instance=hospital, local_leader_user=request.user)
    
    context = {
        'user_form': user_form,
        'hospital_form': hospital_form,
        'hospital': hospital
    }
    
    return render(request, 'accounts/edit_hospital.html', context)
