from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from datetime import datetime, timedelta

from .models import Appointment
from .forms import AppointmentForm, AppointmentUpdateForm
from accounts.models import User, Adopter
from children.models import AdoptionApplication
from notifications.models import Notification
from audit.models import AuditLog
from accounts.models import DistrictAdmin, LocalLeader

@login_required
def appointment_list(request):
    """View to list all appointments based on user role."""
    user = request.user
    appointments = Appointment.objects.all()
    
    # Filter based on user type
    if user.user_type == 'district_admin':
        # Filter by district admin
        appointments = appointments.filter(district_admin=user)
    elif user.user_type == 'local_leader':
        local_leader = LocalLeader.objects.get(user=user)
        # Filter for appointments where the child is in the local leader's area
        # Filter by sector, cell, and district match instead of direct foreign key
        appointments = appointments.filter(
            Q(child__sector=local_leader.sector) & 
            Q(child__district=local_leader.district)
        )
    elif user.user_type == 'adopter':
        adopter = Adopter.objects.get(user=user)
        appointments = appointments.filter(adopter=adopter)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        appointments = appointments.filter(
            Q(child__name__icontains=search_query) |
            Q(adopter__user__username__icontains=search_query) |
            Q(status__icontains=search_query)
        )
    
    # Order by appointment date
    appointments = appointments.order_by('appointment_date')
    
    # Pagination
    paginator = Paginator(appointments, 10)  # 10 appointments per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Create audit log
    AuditLog.objects.create(
        user=user,
        action='view',
        model_name='Appointment',
        object_id=0,  # Using 0 for list views
        object_repr='Appointments List',
        reason=f'Viewed appointments list'
    )
    
    context = {
        'appointments': page_obj,
        'search_query': search_query,
    }
    return render(request, 'appointments/appointment_list.html', context)

@login_required
def appointment_detail(request, pk):
    """View to see details of a specific appointment."""
    appointment = get_object_or_404(Appointment, pk=pk)
    user = request.user
    
    # Check if user has permission to view this appointment
    if user.user_type == 'district_admin':
        # District admin can see all appointments
        pass
    elif user.user_type == 'adopter':
        # Adopters can see their own appointments
        adopter = Adopter.objects.get(user=user)
        if appointment.adopter != adopter:
            messages.error(request, "You do not have permission to view this appointment.")
            return redirect('appointments:appointment_list')
    else:
        # Local leaders and hospitals cannot see appointments
        messages.error(request, "You do not have permission to view appointments.")
        return redirect('dashboard:dashboard')
    
    # Create audit log
    AuditLog.objects.create(
        user=user,
        action='view',
        model_name='Appointment',
        object_id=appointment.id,
        object_repr=f'Appointment for {appointment.adopter.user.get_full_name}',
        reason=f'Viewed appointment details'
    )
    
    return render(request, 'appointments/appointment_detail.html', {'appointment': appointment})

@login_required
def appointment_create(request):
    """View to create a new appointment."""
    user = request.user
    
    # Only district admin can create appointments
    if user.user_type != 'district_admin':
        messages.error(request, "You do not have permission to create appointments.")
        return redirect('dashboard:dashboard')
    
    # Check if creating from an application
    application_id = request.GET.get('application_id')
    
    if request.method == 'POST':
        form = AppointmentForm(request.POST, application_id=application_id)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.district_admin = user
            appointment.save()
            
            # Update the application with meeting info
            application = appointment.application
            application.meeting_appointment = appointment.appointment_date
            application.meeting_status = 'scheduled'
            application.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=user,
                action='create',
                model_name='Appointment',
                object_id=appointment.id,
                object_repr=f'Appointment for {appointment.adopter.user.get_full_name}',
                reason=f'Created appointment with {appointment.adopter.user.get_full_name} for {appointment.child.name}'
            )
            
            # Create notification for the adopter
            Notification.objects.create(
                recipient=appointment.adopter.user,
                sender=user,
                title='New Appointment Scheduled',
                message=f'An appointment has been scheduled for your adoption application for {appointment.child.name} on {appointment.appointment_date.strftime("%B %d, %Y at %I:%M %p")}.',
                related_link=f'/appointments/{appointment.id}/'
            )
            
            messages.success(request, "Appointment created successfully.")
            return redirect('appointments:appointment_detail', pk=appointment.id)
    else:
        form = AppointmentForm(application_id=application_id)
    
    return render(request, 'appointments/appointment_form.html', {
        'form': form,
        'title': 'Create Appointment'
    })

@login_required
def appointment_update(request, pk):
    """View to update an existing appointment."""
    appointment = get_object_or_404(Appointment, pk=pk)
    user = request.user
    
    # Only district admin can update appointments
    if user.user_type != 'district_admin':
        messages.error(request, "You do not have permission to update appointments.")
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        form = AppointmentUpdateForm(request.POST, instance=appointment)
        if form.is_valid():
            old_date = appointment.appointment_date
            old_status = appointment.status
            
            appointment = form.save()
            
            # Update related application
            if old_status != appointment.status or old_date != appointment.appointment_date:
                application = appointment.application
                
                if appointment.status == 'cancelled':
                    application.meeting_status = 'canceled'
                elif appointment.status == 'completed':
                    application.meeting_status = 'completed'
                else:
                    application.meeting_status = 'scheduled'
                
                application.meeting_appointment = appointment.appointment_date
                application.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=user,
                action='update',
                model_name='Appointment',
                object_id=appointment.id,
                object_repr=f'Appointment for {appointment.adopter.user.get_full_name}',
                reason=f'Updated appointment with {appointment.adopter.user.get_full_name} for {appointment.child.name}'
            )
            
            # Create notification for the adopter
            notification_title = 'Appointment Updated'
            notification_message = f'Your appointment for the adoption of {appointment.child.name} has been updated.'
            
            if old_date != appointment.appointment_date:
                notification_message += f' New date: {appointment.appointment_date.strftime("%B %d, %Y at %I:%M %p")}.'
            
            if old_status != appointment.status:
                notification_message += f' Status updated to: {appointment.get_status_display()}.'
            
            Notification.objects.create(
                recipient=appointment.adopter.user,
                sender=user,
                title=notification_title,
                message=notification_message,
                related_link=f'/appointments/{appointment.id}/'
            )
            
            messages.success(request, "Appointment updated successfully.")
            return redirect('appointments:appointment_detail', pk=appointment.id)
    else:
        form = AppointmentUpdateForm(instance=appointment)
    
    return render(request, 'appointments/appointment_form.html', {
        'form': form,
        'title': 'Update Appointment',
        'appointment': appointment
    })

@login_required
def appointment_cancel(request, pk):
    """View to cancel an appointment."""
    appointment = get_object_or_404(Appointment, pk=pk)
    user = request.user
    
    # Check if user has permission to cancel this appointment
    if user.user_type == 'district_admin':
        # District admin can cancel any appointment
        pass
    elif user.user_type == 'adopter':
        # Adopters can cancel their own appointments
        adopter = Adopter.objects.get(user=user)
        if appointment.adopter != adopter:
            messages.error(request, "You do not have permission to cancel this appointment.")
            return redirect('appointments:appointment_list')
    else:
        # Local leaders and hospitals cannot cancel appointments
        messages.error(request, "You do not have permission to cancel appointments.")
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        
        # Update appointment status
        appointment.status = 'cancelled'
        appointment.notes += f"\n\nCancelled by {user.username} on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        if reason:
            appointment.notes += f"\nReason: {reason}"
        appointment.save()
        
        # Update related application
        application = appointment.application
        application.meeting_status = 'canceled'
        application.save()
        
        # Create audit log
        AuditLog.objects.create(
            user=user,
            action='update',
            model_name='Appointment',
            object_id=appointment.id,
            object_repr=f'Appointment for {appointment.adopter.user.get_full_name}',
            reason=f'Cancelled appointment with {appointment.adopter.user.get_full_name} for {appointment.child.name}. Reason: {reason}'
        )
        
        # Create notification
        if user.user_type == 'district_admin':
            # Notify the adopter
            Notification.objects.create(
                recipient=appointment.adopter.user,
                sender=user,
                title='Appointment Cancelled',
                message=f'Your appointment for the adoption of {appointment.child.name} has been cancelled by the district admin.',
                related_link=f'/appointments/{appointment.id}/'
            )
        else:  # adopter
            # Notify the district admin
            Notification.objects.create(
                recipient=appointment.district_admin,
                sender=user,
                title='Appointment Cancelled',
                message=f'The appointment with {appointment.adopter.full_name} for the adoption of {appointment.child.name} has been cancelled by the adopter.',
                related_link=f'/appointments/{appointment.id}/'
            )
        
        messages.success(request, "Appointment cancelled successfully.")
        return redirect('appointments:appointment_list')
    
    return render(request, 'appointments/appointment_cancel.html', {'appointment': appointment})
