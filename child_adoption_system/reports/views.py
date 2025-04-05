from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import transaction

from .models import Report
from .forms import ReportForm, ReportUpdateForm, AbandonedChildReportForm, ChildAdoptionApprovalForm
from accounts.models import LocalLeader, Hospital
from notifications.models import Notification
from audit.models import AuditLog
from children.models import Child

# Create your views here.

@login_required
def report_list(request):
    """View to list all reports based on user role."""
    user = request.user
    
    # Different queries based on user type
    if user.user_type == 'district_admin':
        # District admin can see all reports
        reports = Report.objects.all().order_by('-report_date')
        
        # Filter by hospital if specified
        hospital_filter = request.GET.get('hospital', '')
        if hospital_filter:
            reports = reports.filter(reported_by_id=hospital_filter)
            
    elif user.user_type == 'local_leader':
        # Local leader can see reports they created and from hospitals in their area
        local_leader = LocalLeader.objects.get(user=user)
        hospital_users = Hospital.objects.filter(local_leader=local_leader).values_list('user_id', flat=True)
        reports = Report.objects.filter(
            Q(reported_by=user) | Q(reported_by_id__in=hospital_users)
        ).order_by('-report_date')
        
        # Filter by hospital if specified
        hospital_filter = request.GET.get('hospital', '')
        if hospital_filter and (hospital_filter == str(user.id) or int(hospital_filter) in hospital_users):
            reports = reports.filter(reported_by_id=hospital_filter)
            
    elif user.user_type == 'hospital':
        # Hospital users should only see reports they created
        reports = Report.objects.filter(reported_by=user).order_by('-report_date')
        
        # Get reports created through the abandoned child form
        # These are associated with children that have a found_location_type
        reports = reports.filter(child__found_location_type__isnull=False)
        
    else:  # Adopter
        # Adopters cannot see reports
        messages.error(request, "You do not have permission to view reports.")
        return redirect('dashboard:dashboard')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        reports = reports.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(reports, 10)  # 10 reports per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'reports/report_list.html', {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'status_choices': Report.REPORT_STATUS_CHOICES,
    })

@login_required
def report_detail(request, pk):
    """View to see details of a specific report."""
    report = get_object_or_404(Report, pk=pk)
    user = request.user
    
    # Check if user has permission to view this report
    if user.user_type == 'district_admin':
        # District admin can see all reports
        pass
    elif user.user_type == 'local_leader':
        # Local leader can see reports they created and from hospitals in their area
        local_leader = LocalLeader.objects.get(user=user)
        hospital_users = Hospital.objects.filter(local_leader=local_leader).values_list('user_id', flat=True)
        if report.reported_by != user and report.reported_by.id not in hospital_users:
            messages.error(request, "You do not have permission to view this report.")
            return redirect('reports:report_list')
    elif user.user_type == 'hospital':
        # Hospital can see reports they created
        if report.reported_by != user:
            messages.error(request, "You do not have permission to view this report.")
            return redirect('reports:report_list')
    else:  # Adopter
        # Adopters cannot see reports
        messages.error(request, "You do not have permission to view reports.")
        return redirect('dashboard:dashboard')
    
    # Create audit log
    AuditLog.objects.create(
        user=user,
        action='update',
        model_name='Report',
        object_id=report.id,
        object_repr=f'Report {report.id}',
        reason=f'User {user.username} viewed report {report.id} for {report.child.name}'
    )
    
    # Update form for district admin
    update_form = None
    if user.user_type == 'district_admin':
        update_form = ReportUpdateForm(instance=report)
    
    return render(request, 'reports/report_detail.html', {
        'report': report,
        'update_form': update_form
    })

@login_required
def report_abandoned_child(request):
    """View to report an abandoned child - creates both child and report."""
    user = request.user
    
    # Only hospital and local leader can create reports
    if user.user_type not in ['hospital', 'local_leader']:
        messages.error(request, "You do not have permission to report abandoned children.")
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        form = AbandonedChildReportForm(request.POST, request.FILES, user=user)
        if form.is_valid():
            report = form.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=user,
                action='create',
                model_name='Report',
                object_id=report.id,
                object_repr=f'Report {report.id}',
                reason=f'User {user.username} reported abandoned child: {report.child.name}'
            )
            
            # Create notifications
            if user.user_type == 'hospital':
                # Notify local leader
                hospital = Hospital.objects.get(user=user)
                local_leader_user = hospital.local_leader.user
                Notification.objects.create(
                    recipient=local_leader_user,
                    sender=user,
                    title='New Abandoned Child Report',
                    message=f'Hospital {user.username} has reported an abandoned child: {report.child.name}.',
                    related_link=f'/reports/{report.id}/'
                )
                
                # Also notify district admin directly
                district_admin_user = hospital.local_leader.district_admin.user
                Notification.objects.create(
                    recipient=district_admin_user,
                    sender=user,
                    title='New Abandoned Child Report',
                    message=f'Hospital {user.username} has reported an abandoned child: {report.child.name}.',
                    related_link=f'/reports/{report.id}/'
                )
            else:  # local_leader
                # Notify district admin
                local_leader = LocalLeader.objects.get(user=user)
                district_admin_user = local_leader.district_admin.user
                Notification.objects.create(
                    recipient=district_admin_user,
                    sender=user,
                    title='New Abandoned Child Report',
                    message=f'Local Leader {user.username} has reported an abandoned child: {report.child.name}.',
                    related_link=f'/reports/{report.id}/'
                )
            
            messages.success(request, "Abandoned child report submitted successfully.")
            return redirect('reports:report_detail', pk=report.id)
    else:
        form = AbandonedChildReportForm(user=user)
    
    return render(request, 'reports/abandoned_child_report_form.html', {'form': form})

@login_required
def report_create(request):
    """View to create a new report for an existing child."""
    user = request.user
    
    # Only hospital and local leader can create reports
    if user.user_type not in ['hospital', 'local_leader']:
        messages.error(request, "You do not have permission to create reports.")
        return redirect('dashboard:dashboard')
    
    if request.method == 'POST':
        form = ReportForm(request.POST, user=user)
        if form.is_valid():
            report = form.save(commit=False)
            report.reported_by = user
            report.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=user,
                action='create',
                model_name='Report',
                object_id=report.id,
                object_repr=f'Report {report.id}',
                reason=f'User {user.username} created a new report for {report.child.name}'
            )
            
            # Create notification
            if user.user_type == 'hospital':
                # Notify local leader
                hospital = Hospital.objects.get(user=user)
                local_leader_user = hospital.local_leader.user
                Notification.objects.create(
                    recipient=local_leader_user,
                    sender=user,
                    title='New Abandoned Child Report',
                    message=f'Hospital {user.username} has reported an abandoned child: {report.child.name}.',
                    related_link=f'/reports/{report.id}/'
                )
                
                # Also notify district admin directly
                district_admin_user = hospital.local_leader.district_admin.user
                Notification.objects.create(
                    recipient=district_admin_user,
                    sender=user,
                    title='New Abandoned Child Report',
                    message=f'Hospital {user.username} has reported an abandoned child: {report.child.name}.',
                    related_link=f'/reports/{report.id}/'
                )
            else:  # local_leader
                # Notify district admin
                local_leader = LocalLeader.objects.get(user=user)
                district_admin_user = local_leader.district_admin.user
                Notification.objects.create(
                    recipient=district_admin_user,
                    sender=user,
                    title='New Abandoned Child Report',
                    message=f'Local Leader {user.username} has reported an abandoned child: {report.child.name}.',
                    related_link=f'/reports/{report.id}/'
                )
            
            messages.success(request, "Report created successfully.")
            return redirect('reports:report_detail', pk=report.id)
    else:
        form = ReportForm(user=user)
    
    return render(request, 'reports/report_form.html', {'form': form, 'title': 'Create Report'})

@login_required
def report_update(request, pk):
    """View to update a report (for district admin only)."""
    report = get_object_or_404(Report, pk=pk)
    user = request.user
    
    # Only district admin can update reports
    if user.user_type != 'district_admin':
        messages.error(request, "You do not have permission to update reports.")
        return redirect('reports:report_list')
    
    if request.method == 'POST':
        form = ReportUpdateForm(request.POST, instance=report)
        if form.is_valid():
            old_status = report.status
            updated_report = form.save()
            
            # Create audit log
            AuditLog.objects.create(
                user=user,
                action='update',
                model_name='Report',
                object_id=report.id,
                object_repr=f'Report {report.id}',
                reason=f'User {user.username} updated report {report.id} for {report.child.name}'
            )
            
            # Create notification for the reporter
            Notification.objects.create(
                recipient=report.reported_by,
                sender=user,
                title='Report Status Update',
                message=f'Your report for {report.child.name} has been updated to {report.get_status_display()}.',
                related_link=f'/reports/{report.id}/'
            )
            
            # If the reporter is a hospital, also notify their local leader
            if report.reported_by.user_type == 'hospital':
                hospital = Hospital.objects.get(user=report.reported_by)
                local_leader_user = hospital.local_leader.user
                
                # Don't notify if the local leader is already the reporter
                if local_leader_user != report.reported_by:
                    Notification.objects.create(
                        recipient=local_leader_user,
                        sender=user,
                        title='Hospital Report Status Update',
                        message=f'A report from {report.reported_by.username} for {report.child.name} has been updated to {report.get_status_display()}.',
                        related_link=f'/reports/{report.id}/'
                    )
            
            messages.success(request, f'Report for {report.child.name} updated successfully.')
            return redirect('reports:report_detail', pk=report.id)
    else:
        form = ReportUpdateForm(instance=report)
    
    return render(request, 'reports/report_form.html', {
        'form': form,
        'title': 'Update Report',
        'report': report
    })

@login_required
def report_delete(request, pk):
    """View to delete a report (for district admin only)."""
    report = get_object_or_404(Report, pk=pk)
    user = request.user
    
    # Only district admin can delete reports
    if user.user_type != 'district_admin':
        messages.error(request, "You do not have permission to delete reports.")
        return redirect('reports:report_list')
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        child_name = report.child.name
        reporter = report.reported_by.username
        
        # Create audit log
        AuditLog.objects.create(
            user=user,
            action='delete',
            model_name='Report',
            object_id=report.id,
            object_repr=f'Report for {child_name}',
            reason=f'User {user.username} deleted report for {child_name} by {reporter}. Reason: {reason}'
        )
        
        report.delete()
        messages.success(request, f'Report for {child_name} deleted successfully.')
        return redirect('reports:report_list')
    
    return render(request, 'reports/report_confirm_delete.html', {'report': report})

@login_required
def review_child_adoption(request, report_id):
    """View for district admin to review reports and approve children for adoption."""
    user = request.user
    
    # Only district admin can approve children for adoption
    if user.user_type != 'district_admin':
        messages.error(request, "You do not have permission to approve children for adoption.")
        return redirect('dashboard:dashboard')
    
    report = get_object_or_404(Report, pk=report_id)
    child = report.child
    
    if request.method == 'POST':
        # Get data directly from POST
        child_status = request.POST.get('status')
        admin_notes = request.POST.get('admin_notes', '')
        district_admin_notes = request.POST.get('district_admin_notes', '')
        
        print(f"POST data received: {request.POST}")
        print(f"Child status: {child_status}")
        
        # Basic validation
        if not child_status:
            messages.error(request, "Please select a status for the child.")
            return redirect('reports:review_child_adoption', report_id=report_id)
        
        if child_status == 'available' and not admin_notes:
            messages.error(request, "Admin notes are required when making a child available for adoption.")
            return redirect('reports:review_child_adoption', report_id=report_id)
        
        try:
            # SIMPLIFIED APPROACH: Directly update the models
            
            # Step 1: Update the child first
            previous_status = child.status
            child.status = child_status
            child.admin_notes = admin_notes
            child.save()
            
            # Step 2: Update the report and handle forced resolution
            report.district_admin_notes = district_admin_notes
            force_resolved = request.POST.get('force_resolved') == 'true'
            
            # Step 3: Check actual saved child status and set appropriate report status
            print(f"DEBUG - Child status after save: {child.status}")
            
            # Always respect when child is available or force_resolved is set
            if child.status == 'available' or force_resolved:
                # Child is available, always set report to resolved
                report.status = 'resolved'
                success_message = f"Success! {child.name} is now available for adoption and will be visible to potential adopters."
                print(f"DEBUG - Setting child as AVAILABLE with message: {success_message}")
            else:
                # For pending child status, set report to reviewed
                report.status = 'reviewed'
                success_message = f"{child.name} remains in pending status and is not visible to adopters yet."
                print(f"DEBUG - Keeping child as PENDING with message: {success_message}")
            
            report.save()
            
            # Step 4: Create audit log
            AuditLog.objects.create(
                user=user,
                action='update',
                model_name='Child',
                object_id=child.id,
                object_repr=f'Child {child.name}',
                reason=f'User {user.username} updated child status from {previous_status} to {child.status}'
            )
            
            # Step 5: Create notification with correct status message
            if child.status == 'available':
                notification_message = f"Your report for {child.name} has been reviewed. The child is now available for adoption."
            else:
                notification_message = f"Your report for {child.name} has been reviewed. The child remains in pending status."
                
            Notification.objects.create(
                recipient=report.reported_by,
                sender=user,
                title='Child Report Review',
                message=notification_message,
                related_link=f'/reports/{report.id}/'
            )
            
            # Final step: Return with success message
            messages.success(request, success_message)
            return redirect('reports:report_detail', pk=report.id)
        
        except Exception as e:
            print(f"Error: {str(e)}")
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('reports:review_child_adoption', report_id=report_id)
    
    # Display form    
    approval_form = ChildAdoptionApprovalForm(instance=child)
    report_form = ReportUpdateForm(instance=report)
    
    return render(request, 'reports/review_child_adoption.html', {
        'report': report,
        'child': child,
        'approval_form': approval_form,
        'report_form': report_form
    })
