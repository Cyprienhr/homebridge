from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import User, Adopter, LocalLeader, Hospital
from children.models import Child, AdoptionApplication
from reports.models import Report
from notifications.models import Notification
from django.db.models import Count, Q
from datetime import datetime, timedelta
from appointments.models import Appointment
from audit.models import AuditLog
from django.utils import timezone
import json

def home(request):
    """View for the home/landing page of the application."""
    # Count statistics for display on the homepage
    available_children = Child.objects.filter(status='available').count()
    total_adoptions = AdoptionApplication.objects.filter(application_status='approved').count()
    
    context = {
        'available_children': available_children,
        'total_adoptions': total_adoptions,
    }
    
    return render(request, 'home.html', context)

@login_required
def dashboard(request):
    """Redirect users to their respective dashboards based on user type."""
    user_type = request.user.user_type
    
    if user_type == 'district_admin':
        return redirect('dashboard:admin_dashboard')
    elif user_type == 'local_leader':
        return redirect('dashboard:local_leader_dashboard')
    elif user_type == 'hospital':
        return redirect('dashboard:hospital_dashboard')
    elif user_type == 'adopter':
        return redirect('dashboard:adopter_dashboard')
    else:
        return redirect('home')

@login_required
def admin_dashboard(request):
    """Dashboard view for district admins."""
    # Get current user
    user = request.user
    
    # Ensure the user is a district admin
    if user.user_type != 'district_admin':
        return redirect('dashboard:dashboard')
    
    # Get recent data for display
    recent_children = Child.objects.all().order_by('-created_at')[:5]
    recent_applications = AdoptionApplication.objects.all().order_by('-created_at')[:5]
    recent_reports = Report.objects.all().order_by('-report_date')[:5]
    upcoming_appointments = Appointment.objects.filter(
        appointment_date__gte=timezone.now(),
        status__in=['pending', 'approved']
    ).order_by('appointment_date')[:5]
    
    # Get counts for dashboard widgets
    children_count = Child.objects.count()
    available_children = Child.objects.filter(status='available').count()
    adopted_children = Child.objects.filter(status='adopted').count()
    pending_children = Child.objects.filter(status='pending').count()
    
    applications_count = AdoptionApplication.objects.count()
    pending_applications = AdoptionApplication.objects.filter(application_status='pending').count()
    approved_applications = AdoptionApplication.objects.filter(application_status='approved').count()
    rejected_applications = AdoptionApplication.objects.filter(application_status='rejected').count()
    
    appointments_count = Appointment.objects.count()
    upcoming_count = Appointment.objects.filter(
        appointment_date__gte=timezone.now(),
        status__in=['pending', 'approved']
    ).count()
    
    users_count = User.objects.count()
    adopters_count = Adopter.objects.count()
    local_leaders_count = LocalLeader.objects.count()
    hospitals_count = Hospital.objects.count()
    
    # Get unread notifications
    unread_notifications = Notification.objects.filter(
        recipient=user,
        read=False
    ).order_by('-created_at')[:5]
    
    context = {
        'recent_children': recent_children,
        'recent_applications': recent_applications,
        'recent_reports': recent_reports,
        'upcoming_appointments': upcoming_appointments,
        'unread_notifications': unread_notifications,
        
        # Counts for dashboard widgets
        'children_count': children_count,
        'available_children': available_children,
        'adopted_children': adopted_children,
        'pending_children': pending_children,
        
        'applications_count': applications_count,
        'pending_applications': pending_applications,
        'approved_applications': approved_applications,
        'rejected_applications': rejected_applications,
        
        'appointments_count': appointments_count,
        'upcoming_count': upcoming_count,
        
        'users_count': users_count,
        'adopters_count': adopters_count,
        'local_leaders_count': local_leaders_count,
        'hospitals_count': hospitals_count,
    }
    
    return render(request, 'dashboards/admin_dashboard.html', context)

@login_required
def local_leader_dashboard(request):
    """Dashboard view for local leaders."""
    # Get current user
    user = request.user
    
    # Ensure the user is a local leader
    if user.user_type != 'local_leader':
        return redirect('dashboard:dashboard')
    
    try:
        local_leader = LocalLeader.objects.get(user=user)
    except LocalLeader.DoesNotExist:
        return redirect('dashboard:dashboard')
    
    # Get hospitals in local leader's area
    hospitals = Hospital.objects.filter(local_leader=local_leader)
    
    # Get reports from this local leader and their hospitals
    hospital_users = hospitals.values_list('user_id', flat=True)
    reports = Report.objects.filter(
        Q(reported_by=user) | Q(reported_by_id__in=hospital_users)
    ).order_by('-report_date')[:5]
    
    # Get children reported in this area
    children = Child.objects.filter(
        Q(reported_by=user) | 
        Q(reported_by_id__in=hospital_users) |
        Q(sector=local_leader.sector, district=local_leader.district)
    ).order_by('-created_at')[:5]
    
    # Get counts for dashboard widgets
    hospitals_count = hospitals.count()
    reports_count = Report.objects.filter(
        Q(reported_by=user) | Q(reported_by_id__in=hospital_users)
    ).count()
    
    # Get unread notifications
    unread_notifications = Notification.objects.filter(
        recipient=user,
        read=False
    ).order_by('-created_at')[:5]
    
    context = {
        'local_leader': local_leader,
        'hospitals': hospitals,
        'reports': reports,
        'children': children,
        'unread_notifications': unread_notifications,
        
        # Counts for dashboard widgets
        'hospitals_count': hospitals_count,
        'reports_count': reports_count,
    }
    
    return render(request, 'dashboards/local_leader_dashboard.html', context)

@login_required
def hospital_dashboard(request):
    """Dashboard view for hospitals."""
    # Get current user
    user = request.user
    
    # Ensure the user is a hospital
    if user.user_type != 'hospital':
        return redirect('dashboard:dashboard')
    
    try:
        hospital = Hospital.objects.get(user=user)
    except Hospital.DoesNotExist:
        return redirect('dashboard:dashboard')
    
    # Get reports created by this hospital
    reports = Report.objects.filter(reported_by=user).order_by('-report_date')[:5]
    recent_reports = reports  # For template consistency
    
    # Get children reported by this hospital
    children = Child.objects.filter(
        Q(reported_by=user) | Q(hospital__user=user)
    ).order_by('-created_at')[:5]
    
    # Get counts for dashboard widgets
    reports_count = Report.objects.filter(reported_by=user).count()
    children_count = Child.objects.filter(
        Q(reported_by=user) | Q(hospital__user=user)
    ).count()
    
    # Gender distribution for children
    male_count = Child.objects.filter(
        (Q(reported_by=user) | Q(hospital__user=user)),
        gender='male'
    ).count()
    
    female_count = Child.objects.filter(
        (Q(reported_by=user) | Q(hospital__user=user)),
        gender='female'
    ).count()
    
    # Additional data needed by the template
    newborns_count = children_count
    abandoned_count = Child.objects.filter(
        (Q(reported_by=user) | Q(hospital__user=user)),
        found_location_type='hospital'
    ).count()
    staff_count = 1  # Default to 1 (the hospital user)
    
    # Monthly data for charts - get data for last 6 months
    current_date = timezone.now().date()
    monthly_data = []
    
    for i in range(5, -1, -1):
        month_start = (current_date.replace(day=1) - timedelta(days=30*i))
        month_end = (month_start.replace(day=28) + timedelta(days=4))
        month_end = month_end - timedelta(days=month_end.day)  # Last day of the month
        
        regular_count = Child.objects.filter(
            (Q(reported_by=user) | Q(hospital__user=user)),
            created_at__gte=month_start,
            created_at__lte=month_end,
            found_location_type='hospital'
        ).count()
        
        abandoned_count_month = Child.objects.filter(
            (Q(reported_by=user) | Q(hospital__user=user)),
            created_at__gte=month_start,
            created_at__lte=month_end,
            found_location_type='street'
        ).count()
        
        monthly_data.append({
            "month": month_start.strftime("%b"),
            "regular": regular_count,
            "abandoned": abandoned_count_month
        })
    
    # Convert to JSON for JavaScript
    monthly_data_json = json.dumps(monthly_data)
    
    # Mock recent newborns - in the future, we'll create a proper model for this
    recent_newborns = [{
        'id': 1,
        'dob': timezone.now().date() - timedelta(days=3),
        'hospital_id': f"H{hospital.id}-N001",
        'gender': 'male',
        'is_abandoned': False
    }, {
        'id': 2,
        'dob': timezone.now().date() - timedelta(days=5),
        'hospital_id': f"H{hospital.id}-N002",
        'gender': 'female',
        'is_abandoned': True
    }] if children_count > 0 else []
    
    # Get audit logs for this hospital
    audit_logs = AuditLog.objects.filter(user=user).order_by('-created_at')[:5]
    
    # Get unread notifications
    unread_notifications = Notification.objects.filter(
        recipient=user,
        read=False
    ).order_by('-created_at')[:5]
    
    context = {
        'hospital': hospital,
        'reports': reports,
        'recent_reports': recent_reports,
        'children': children,
        'unread_notifications': unread_notifications,
        
        # Counts for dashboard widgets
        'reports_count': reports_count,
        'children_count': children_count,
        'newborns_count': newborns_count,
        'abandoned_count': abandoned_count,
        'staff_count': staff_count,
        
        # Data for charts
        'male_count': male_count,
        'female_count': female_count,
        'monthly_data': monthly_data_json,
        
        # Mock data
        'recent_newborns': recent_newborns,
        'audit_logs': audit_logs,
    }
    
    return render(request, 'dashboards/hospital_dashboard.html', context)

@login_required
def adopter_dashboard(request):
    """Dashboard view for adopters."""
    # Get current user
    user = request.user
    
    # Ensure the user is an adopter
    if user.user_type != 'adopter':
        return redirect('dashboard:dashboard')
    
    try:
        adopter = Adopter.objects.get(user=user)
    except Adopter.DoesNotExist:
        return redirect('dashboard:dashboard')
    
    # Get available children for adoption
    available_children = Child.objects.filter(status='available').order_by('-created_at')[:5]
    
    # Get adoption applications for this adopter
    applications = AdoptionApplication.objects.filter(adopter=adopter).order_by('-created_at')
    
    # Get upcoming appointments
    appointments = Appointment.objects.filter(
        adopter=adopter,
        appointment_date__gte=timezone.now(),
        status__in=['pending', 'approved']
    ).order_by('appointment_date')[:5]
    
    # Get counts for dashboard widgets
    applications_count = applications.count()
    pending_applications = applications.filter(application_status='pending').count()
    approved_applications = applications.filter(application_status='approved').count()
    rejected_applications = applications.filter(application_status='rejected').count()
    
    appointments_count = Appointment.objects.filter(adopter=adopter).count()
    upcoming_count = Appointment.objects.filter(
        adopter=adopter,
        appointment_date__gte=timezone.now(),
        status__in=['pending', 'approved']
    ).count()
    
    # Get unread notifications
    unread_notifications = Notification.objects.filter(
        recipient=user,
        read=False
    ).order_by('-created_at')[:5]
    
    context = {
        'adopter': adopter,
        'available_children': available_children,
        'applications': applications,
        'appointments': appointments,
        'unread_notifications': unread_notifications,
        
        # Counts for dashboard widgets
        'applications_count': applications_count,
        'pending_applications': pending_applications,
        'approved_applications': approved_applications,
        'rejected_applications': rejected_applications,
        
        'appointments_count': appointments_count,
        'upcoming_count': upcoming_count,
    }
    
    return render(request, 'dashboards/adopter_dashboard.html', context)

def get_activity_icon(action_type):
    """Helper function to get the appropriate icon for an activity type."""
    icon_map = {
        'create': 'fa-plus-circle',
        'update': 'fa-edit',
        'delete': 'fa-trash',
        'view': 'fa-eye',
        'login': 'fa-sign-in-alt',
        'logout': 'fa-sign-out-alt',
        'default': 'fa-info-circle'
    }
    return icon_map.get(action_type, icon_map['default'])
