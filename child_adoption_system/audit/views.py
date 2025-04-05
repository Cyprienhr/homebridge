from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView
from django.core.paginator import Paginator
from django.db.models import Q
from .models import AuditLog

# Create your views here.

class AuditLogListView(ListView):
    model = AuditLog
    template_name = 'audit/trash_list.html'
    context_object_name = 'audit_logs'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'district_admin':
            return AuditLog.objects.all().order_by('-created_at')
        elif user.user_type == 'local_leader':
            return AuditLog.objects.filter(user__local_leader_profile__district_admin=user.district_admin_profile).order_by('-created_at')
        elif user.user_type == 'hospital':
            return AuditLog.objects.filter(user=user).order_by('-created_at')
        return AuditLog.objects.none()

@login_required
def audit_log_list(request):
    """View to list audit logs (for district admin only)."""
    user = request.user
    
    # Only district admin can view audit logs
    if user.user_type != 'district_admin':
        return render(request, 'audit/access_denied.html')
    
    # Get all audit logs
    audit_logs = AuditLog.objects.all().order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        audit_logs = audit_logs.filter(
            Q(user__username__icontains=search_query) |
            Q(action__icontains=search_query) |
            Q(model_name__icontains=search_query) |
            Q(object_repr__icontains=search_query) |
            Q(reason__icontains=search_query)
        )
    
    # Filter by action type
    action_filter = request.GET.get('action', '')
    if action_filter:
        audit_logs = audit_logs.filter(action=action_filter)
    
    # Filter by user
    user_filter = request.GET.get('user', '')
    if user_filter:
        audit_logs = audit_logs.filter(user__username=user_filter)
    
    # Pagination
    paginator = Paginator(audit_logs, 20)  # 20 logs per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get unique users for filter dropdown
    unique_users = AuditLog.objects.values_list('user__username', flat=True).distinct()
    
    return render(request, 'audit/audit_log_list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'action_filter': action_filter,
        'user_filter': user_filter,
        'action_choices': AuditLog.ACTION_CHOICES,
        'unique_users': unique_users,
    })
