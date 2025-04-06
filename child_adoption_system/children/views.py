from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.generic import ListView
from django.views.generic import DetailView
from django.views.generic import CreateView
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from django.views.generic import DeleteView
from django.utils import timezone
from django.db import connection

from .models import Child, AdoptionApplication
from .forms import ChildForm, AdoptionApplicationForm, AdoptionApplicationUpdateForm
from accounts.models import Adopter, Hospital, LocalLeader, User
from notifications.models import Notification
from .forms import ChildForm, AdoptionApplicationForm
from audit.models import AuditLog

# Create your views here.

class ChildListView(ListView):
    model = Child
    template_name = 'children/child_list.html'
    context_object_name = 'children'

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'adopter':
            return Child.objects.filter(status='available')
        return Child.objects.all()

class ChildDetailView(DetailView):
    model = Child
    template_name = 'children/child_detail.html'
    context_object_name = 'child'

class ChildCreateView(CreateView):
    model = Child
    form_class = ChildForm
    template_name = 'children/child_form.html'
    success_url = reverse_lazy('child_list')

    def form_valid(self, form):
        form.instance.reported_by = self.request.user
        return super().form_valid(form)

class ChildUpdateView(UpdateView):
    model = Child
    form_class = ChildForm
    template_name = 'children/child_form.html'
    success_url = reverse_lazy('child_list')

class ChildDeleteView(DeleteView):
    model = Child
    success_url = reverse_lazy('child_list')

@login_required
def apply_adoption(request, pk):
    child = get_object_or_404(Child, pk=pk)
    if request.method == 'POST':
        form = AdoptionApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.adopter = request.user.adopter_profile
            application.child = child
            application.save()
            messages.success(request, 'Application submitted successfully.')
            return redirect('child_list')
    else:
        form = AdoptionApplicationForm()
    
    return render(request, 'children/adoption_status.html', {
        'form': form,
        'child': child
    })

@login_required
def adoption_status(request):
    user = request.user
    if user.user_type == 'adopter':
        applications = AdoptionApplication.objects.filter(adopter=user.adopter_profile)
    elif user.user_type == 'district_admin':
        applications = AdoptionApplication.objects.all()
    else:
        applications = AdoptionApplication.objects.none()
    
    return render(request, 'children/adoption_status.html', {
        'applications': applications
    })

@login_required
def child_list(request):
    """View to display list of children based on user role and filters."""
    user = request.user
    
    # Different queries based on user type
    if user.user_type == 'district_admin':
        # District admin can see all children
        children = Child.objects.all()
    elif user.user_type == 'adopter':
        # Adopters can only see available children
        children = Child.objects.filter(status='available')
        print(f"DEBUG - Available children for adopters: {children.count()}")
        # Check if any children have status='available'
        available_count = Child.objects.filter(status='available').count()
        all_count = Child.objects.all().count()
        print(f"DEBUG - Total available children in DB: {available_count} out of {all_count}")
        # Directly check the database
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM children_child WHERE status = 'available'")
            db_available_count = cursor.fetchone()[0]
            print(f"DEBUG - Direct SQL count of available children: {db_available_count}")
    elif user.user_type == 'local_leader':
        # Local leaders can see children in their sector/district
        try:
            local_leader = user.local_leader
            children = Child.objects.filter(
                Q(sector=local_leader.sector) & 
                Q(district=local_leader.district)
            )
        except:
            children = Child.objects.none()
    elif user.user_type == 'hospital':
        # Hospitals can see children they reported
        try:
            hospital = user.hospital
            children = Child.objects.filter(hospital=hospital)
        except:
            children = Child.objects.none()
    else:
        children = Child.objects.none()
    
    # Apply filters
    status_filter = request.GET.get('status')
    if status_filter:
        children = children.filter(status=status_filter)
    
    gender_filter = request.GET.get('gender')
    if gender_filter:
        children = children.filter(gender=gender_filter)
    
    age_min = request.GET.get('age_min')
    if age_min:
        children = children.filter(age__gte=age_min)
    
    age_max = request.GET.get('age_max')
    if age_max:
        children = children.filter(age__lte=age_max)
    
    search_query = request.GET.get('search')
    if search_query:
        children = children.filter(
            Q(name__icontains=search_query) |
            Q(registration_number__icontains=search_query) |
            Q(district__icontains=search_query) |
            Q(sector__icontains=search_query)
        )
    
    # Order by creation date, newest first
    children = children.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(children, 12)  # Show 12 children per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Create audit log
    AuditLog.objects.create(
        user=user,
        action='view',
        model_name='Child',
        object_id=0,  # Using 0 for list views
        object_repr='Children List',
        reason='Viewed children list'
    )
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'gender_filter': gender_filter,
        'age_min': age_min,
        'age_max': age_max,
        'search_query': search_query,
        'gender_choices': Child.GENDER_CHOICES,
        'status_choices': Child.STATUS_CHOICES,
    }
    
    return render(request, 'children/child_list.html', context)

@login_required
def child_detail(request, pk):
    """View details of a specific child."""
    child = get_object_or_404(Child, pk=pk)
    user = request.user
    
    # Check if user has permission to view
    if user.user_type == 'adopter' and child.status != 'available':
        messages.error(request, "You don't have permission to view this child.")
        return redirect('children:child_list')
    
    # For adopter, check if they have already applied
    has_applied = False
    if user.user_type == 'adopter':
        try:
            adopter = Adopter.objects.get(user=user)
            has_applied = AdoptionApplication.objects.filter(
                adopter=adopter,
                child=child
            ).exists()
        except Adopter.DoesNotExist:
            pass
    
    # Create audit log
    AuditLog.objects.create(
        user=user,
        action='view',
        model_name='Child',
        object_id=child.id,
        object_repr=str(child),
        reason='Viewed child details'
    )
    
    context = {
        'child': child,
        'has_applied': has_applied,
    }
    
    return render(request, 'children/child_detail.html', context)

@login_required
def child_create(request):
    """Create a new child record."""
    user = request.user
    
    # Only district admin and local leaders can create child records
    if user.user_type not in ['district_admin', 'local_leader']:
        messages.error(request, "You don't have permission to create child records.")
        return redirect('children:child_list')
    
    if request.method == 'POST':
        form = ChildForm(request.POST, request.FILES)
        if form.is_valid():
            child = form.save(commit=False)
            child.reported_by = user
            
            # Set status based on user role
            if user.user_type == 'district_admin':
                # District admin created children are immediately available for adoption
                child.status = 'available'
            else:
                # Local leaders created children are set to pending
                child.status = 'pending'
                
            child.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=user,
                action='create',
                model_name='Child',
                object_id=child.id,
                object_repr=str(child),
                reason='Created child record'
            )
            
            # Create notification if local leader creates the child
            if user.user_type == 'local_leader':
                # Notify district admin
                local_leader = LocalLeader.objects.get(user=user)
                district_admin_user = local_leader.district_admin.user
                Notification.objects.create(
                    recipient=district_admin_user,
                    sender=user,
                    title='New Child Record',
                    message=f'Local Leader {user.username} has created a new child record for {child.name}.',
                    related_link=f'/children/{child.id}/'
                )
            
            messages.success(request, f"Child record for {child.name} created successfully.")
            return redirect('children:child_detail', pk=child.id)
    else:
        # Pre-select 'available' status for district admin
        initial_data = {}
        if user.user_type == 'district_admin':
            initial_data = {'status': 'available'}
        form = ChildForm(initial=initial_data)
    
    context = {
        'form': form,
        'title': 'Register New Child'
    }
    
    return render(request, 'children/child_form.html', context)

@login_required
def child_update(request, pk):
    """Update an existing child record."""
    child = get_object_or_404(Child, pk=pk)
    user = request.user
    
    # Only district admin and the user who reported the child can update
    if user.user_type != 'district_admin' and user != child.reported_by:
        messages.error(request, "You don't have permission to update this child record.")
        return redirect('children:child_detail', pk=child.id)
    
    if request.method == 'POST':
        form = ChildForm(request.POST, request.FILES, instance=child)
        if form.is_valid():
            form.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=user,
                action='update',
                model_name='Child',
                object_id=child.id,
                object_repr=str(child),
                reason='Updated child record'
            )
            
            messages.success(request, f"Child record for {child.name} updated successfully.")
            return redirect('children:child_detail', pk=child.id)
    else:
        form = ChildForm(instance=child)
    
    context = {
        'form': form,
        'child': child,
        'title': 'Update Child Record'
    }
    
    return render(request, 'children/child_form.html', context)

@login_required
def child_delete(request, pk):
    """Delete a child record."""
    child = get_object_or_404(Child, pk=pk)
    user = request.user
    
    # Only district admin can delete child records
    if user.user_type != 'district_admin':
        messages.error(request, "You don't have permission to delete child records.")
        return redirect('children:child_detail', pk=child.id)
    
    if request.method == 'POST':
        child_name = child.name
        
        # Create audit log before deletion
        AuditLog.objects.create(
            user=user,
            action='delete',
            model_name='Child',
            object_id=child.id,
            object_repr=str(child),
            reason=request.POST.get('reason', 'No reason provided')
        )
        
        child.delete()
        messages.success(request, f"Child record for {child_name} deleted successfully.")
        return redirect('children:child_list')
    
    context = {
        'child': child,
        'title': 'Delete Child Record'
    }
    
    return render(request, 'children/child_confirm_delete.html', context)

@login_required
def application_create(request, child_id):
    """Create a new adoption application."""
    child = get_object_or_404(Child, pk=child_id)
    user = request.user
    
    # Only adopters can apply
    if user.user_type != 'adopter':
        messages.error(request, "Only adopters can apply for adoption.")
        return redirect('children:child_detail', pk=child_id)
    
    # Check if child is available
    if child.status != 'available':
        messages.error(request, "This child is not available for adoption.")
        return redirect('children:child_detail', pk=child_id)
    
    try:
        adopter = Adopter.objects.get(user=user)
    except Adopter.DoesNotExist:
        messages.error(request, "Adopter profile not found. Please complete your profile first.")
        return redirect('profile')
    
    # Check if already applied
    existing_application = AdoptionApplication.objects.filter(
        adopter=adopter,
        child=child
    ).first()
    
    if existing_application:
        messages.info(request, "You have already applied to adopt this child.")
        return redirect('children:application_detail', pk=existing_application.id)
    
    if request.method == 'POST':
        form = AdoptionApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.adopter = adopter
            application.child = child
            application.save()
            
            # Update child status to pending if this is the first application
            if child.status == 'available':
                child.status = 'pending'
                child.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=user,
                action='create',
                model_name='AdoptionApplication',
                object_id=application.id,
                object_repr=str(application),
                reason='Created adoption application'
            )
            
            # Notify district admin
            district_admins = User.objects.filter(user_type='district_admin')
            for admin in district_admins:
                Notification.objects.create(
                    recipient=admin,
                    sender=user,
                    title='New Adoption Application',
                    message=f'A new adoption application has been submitted by {adopter.full_name} for {child.name}.',
                    related_link=f'/children/applications/{application.id}/'
                )
            
            messages.success(request, "Your adoption application has been submitted successfully.")
            return redirect('children:application_detail', pk=application.id)
    else:
        form = AdoptionApplicationForm()
    
    context = {
        'form': form,
        'child': child,
        'title': 'Submit Adoption Application'
    }
    
    return render(request, 'children/application_form.html', context)

@login_required
def application_list(request):
    """View list of adoption applications."""
    user = request.user
    
    # Different queries based on user type
    if user.user_type == 'district_admin':
        # District admin can see all applications
        applications = AdoptionApplication.objects.all()
    elif user.user_type == 'adopter':
        # Adopters can only see their own applications
        try:
            adopter = Adopter.objects.get(user=user)
            applications = AdoptionApplication.objects.filter(adopter=adopter)
        except Adopter.DoesNotExist:
            applications = AdoptionApplication.objects.none()
    else:
        applications = AdoptionApplication.objects.none()
    
    # Apply filters
    status_filter = request.GET.get('status')
    if status_filter:
        applications = applications.filter(application_status=status_filter)
    
    search_query = request.GET.get('search')
    if search_query:
        applications = applications.filter(
            Q(child__name__icontains=search_query) |
            Q(adopter__full_name__icontains=search_query) |
            Q(reference_number__icontains=search_query)
        )
    
    # Order by creation date, newest first
    applications = applications.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(applications, 10)  # Show 10 applications per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Create audit log
    AuditLog.objects.create(
        user=user,
        action='view',
        model_name='AdoptionApplication',
        object_id=0,  # Using 0 for list views
        object_repr='Applications List',
        reason='Viewed adoption applications list'
    )
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
        'status_choices': AdoptionApplication.STATUS_CHOICES,
    }
    
    return render(request, 'children/application_list.html', context)

@login_required
def application_detail(request, pk):
    """View details of a specific adoption application."""
    application = get_object_or_404(AdoptionApplication, pk=pk)
    user = request.user
    
    # Check if user has permission to view
    if user.user_type == 'adopter':
        try:
            adopter = Adopter.objects.get(user=user)
            if application.adopter != adopter:
                messages.error(request, "You don't have permission to view this application.")
                return redirect('children:application_list')
        except Adopter.DoesNotExist:
            messages.error(request, "You don't have permission to view this application.")
            return redirect('children:application_list')
    elif user.user_type not in ['district_admin']:
        messages.error(request, "You don't have permission to view this application.")
        return redirect('dashboard:dashboard')
    
    # Create audit log
    AuditLog.objects.create(
        user=user,
        action='view',
        model_name='AdoptionApplication',
        object_id=application.id,
        object_repr=str(application),
        reason='Viewed adoption application details'
    )
    
    context = {
        'application': application,
    }
    
    return render(request, 'children/application_detail.html', context)

@login_required
def application_update_status(request, pk):
    """Update status of an adoption application (admin only)."""
    application = get_object_or_404(AdoptionApplication, pk=pk)
    user = request.user
    
    # Only district admin can update application status
    if user.user_type != 'district_admin':
        messages.error(request, "You don't have permission to update application status.")
        return redirect('children:application_detail', pk=pk)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        if status in [s[0] for s in AdoptionApplication.STATUS_CHOICES]:
            old_status = application.application_status
            application.application_status = status
            application.admin_notes = notes
            application.save()
            
            # Update child status if application is approved or rejected
            if status == 'approved':
                application.child.status = 'adopted'
                application.child.save()
                
                # Reject all other applications for this child
                other_applications = AdoptionApplication.objects.filter(
                    child=application.child,
                    application_status='pending'
                ).exclude(id=application.id)
                
                for other_app in other_applications:
                    other_app.application_status = 'rejected'
                    other_app.admin_notes = f"Another application has been approved for this child."
                    other_app.save()
                    
                    # Notify the adopter
                    Notification.objects.create(
                        recipient=other_app.adopter.user,
                        sender=user,
                        title='Adoption Application Rejected',
                        message=f'Your adoption application for {application.child.name} has been rejected because another application has been approved.',
                        related_link=f'/children/applications/{other_app.id}/'
                    )
            
            elif status == 'rejected' and old_status != 'rejected':
                # Check if there are other pending applications for this child
                other_pending = AdoptionApplication.objects.filter(
                    child=application.child,
                    application_status='pending'
                ).exists()
                
                if not other_pending:
                    application.child.status = 'available'
                    application.child.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=user,
                action='update',
                model_name='AdoptionApplication',
                object_id=application.id,
                object_repr=str(application),
                reason=f'Updated application status from {old_status} to {status}'
            )
            
            # Notify the adopter
            Notification.objects.create(
                recipient=application.adopter.user,
                sender=user,
                title=f'Adoption Application {status.capitalize()}',
                message=f'Your adoption application for {application.child.name} has been {status}. {notes}',
                related_link=f'/children/applications/{application.id}/'
            )
            
            messages.success(request, f"Application status updated to {dict(AdoptionApplication.STATUS_CHOICES)[status]}.")
        else:
            messages.error(request, "Invalid status value.")
        
        return redirect('children:application_detail', pk=pk)
    
    context = {
        'application': application,
        'status_choices': AdoptionApplication.STATUS_CHOICES,
    }
    
    return render(request, 'children/application_update_status.html', context)

@login_required
def application_cancel(request, pk):
    """Cancel an adoption application (adopter only)."""
    application = get_object_or_404(AdoptionApplication, pk=pk)
    user = request.user
    
    # Only the adopter who created the application can cancel it
    if user.user_type != 'adopter':
        messages.error(request, "Only adopters can cancel applications.")
        return redirect('children:application_detail', pk=pk)
    
    try:
        adopter = Adopter.objects.get(user=user)
        if application.adopter != adopter:
            messages.error(request, "You can only cancel your own applications.")
            return redirect('children:application_list')
    except Adopter.DoesNotExist:
        messages.error(request, "Adopter profile not found.")
        return redirect('children:application_list')
    
    # Can only cancel pending applications
    if application.application_status != 'pending':
        messages.error(request, "You can only cancel pending applications.")
        return redirect('children:application_detail', pk=pk)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        
        application.application_status = 'cancelled'
        application.adopter_notes = reason
        application.save()
        
        # Check if there are other pending applications for this child
        other_pending = AdoptionApplication.objects.filter(
            child=application.child,
            application_status='pending'
        ).exists()
        
        if not other_pending:
            application.child.status = 'available'
            application.child.save()
        
        # Create audit log
        AuditLog.objects.create(
            user=user,
            action='update',
            model_name='AdoptionApplication',
            object_id=application.id,
            object_repr=str(application),
            reason=f'Cancelled application: {reason}'
        )
        
        # Notify district admin
        district_admins = User.objects.filter(user_type='district_admin')
        for admin in district_admins:
            Notification.objects.create(
                recipient=admin,
                sender=user,
                title='Adoption Application Cancelled',
                message=f'An adoption application for {application.child.name} has been cancelled by {adopter.full_name}. Reason: {reason}',
                related_link=f'/children/applications/{application.id}/'
            )
        
        messages.success(request, "Your application has been cancelled successfully.")
        return redirect('children:application_list')
    
    context = {
        'application': application,
    }
    
    return render(request, 'children/application_cancel.html', context)
