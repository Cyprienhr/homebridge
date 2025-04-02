from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Report
from .forms import ReportForm, ReportUpdateForm
from accounts.models import LocalLeader, Hospital
from notifications.models import Notification
from audit.models import AuditLog

# Create your views here.

@login_required
def report_list(request):
    """View to list all reports based on user role."""
    user = request.user
    
    # Different queries based on user type
    if user.user_type == 'district_admin':
        # District admin can see all reports
        reports = Report.objects.all().order_by('-report_date')
    elif user.user_type == 'local_leader':
        # Local leader can see reports they created and from hospitals in their area
        local_leader = LocalLeader.objects.get(user=user)
        hospital_users = Hospital.objects.filter(local_leader=local_leader).values_list('user_id', flat=True)
        reports = Report.objects.filter(
            Q(reported_by=user) | Q(reported_by_id__in=hospital_users)
        ).order_by('-report_date')
    elif user.user_type == 'hospital':
        # Hospital can see reports they created
        reports = Report.objects.filter(reported_by=user).order_by('-report_date')
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
            return redirect('report_list')
    elif user.user_type == 'hospital':
        # Hospital can see reports they created
        if report.reported_by != user:
            messages.error(request, "You do not have permission to view this report.")
            return redirect('report_list')
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
def report_create(request):
    """View to create a new report."""
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
                    title='New Report',
                    message=f'A new report has been created by {user.username} for {report.child.name}.',
                    related_link=f'/reports/{report.id}/'
                )
            else:  # local_leader
                # Notify district admin
                local_leader = LocalLeader.objects.get(user=user)
                district_admin_user = local_leader.district_admin.user
                Notification.objects.create(
                    recipient=district_admin_user,
                    sender=user,
                    title='New Report',
                    message=f'A new report has been created by {user.username} for {report.child.name}.',
                    related_link=f'/reports/{report.id}/'
                )
            
            messages.success(request, "Report created successfully.")
            return redirect('report_detail', pk=report.id)
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
        return redirect('report_list')
    
    if request.method == 'POST':
        form = ReportUpdateForm(request.POST, instance=report)
        if form.is_valid():
            form.save()
            
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
            
            messages.success(request, f'Report {report.title} updated successfully.')
            return redirect('dashboard:dashboard')
    else:
        form = ReportUpdateForm(instance=report)
    
    return render(request, 'reports/report_update.html', {
        'form': form,
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
        return redirect('report_list')
    
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
        messages.success(request, f'Report {report.title} deleted successfully.')
        return redirect('dashboard:dashboard')
    
    return render(request, 'reports/report_confirm_delete.html', {'report': report})
