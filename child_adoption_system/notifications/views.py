from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Count
from django.views.generic import ListView
from .models import Notification
from audit.models import AuditLog

# Create your views here.

class NotificationListView(ListView):
    model = Notification
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

@login_required
def notification_list(request):
    """View to list all notifications for the current user."""
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    
    # Filter by read status
    read_filter = request.GET.get('read', '')
    if read_filter == 'read':
        notifications = notifications.filter(read=True)
    elif read_filter == 'unread':
        notifications = notifications.filter(read=False)
    
    # Pagination
    paginator = Paginator(notifications, 10)  # 10 notifications per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Create audit log
    AuditLog.objects.create(
        user=request.user,
        action='update',
        model_name='Notification',
        object_id=0,
        object_repr='All notifications',
        reason=f'User {request.user.username} viewed notifications'
    )
    
    return render(request, 'notifications/notification_list.html', {
        'page_obj': page_obj,
        'read_filter': read_filter,
        'unread_count': notifications.filter(read=False).count()
    })

@login_required
def notification_detail(request, pk):
    """View to see details of a specific notification."""
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    
    # Mark as read if not already
    if not notification.read:
        notification.mark_as_read()
    
    # Create audit log
    AuditLog.objects.create(
        user=request.user,
        action='update',
        model_name='Notification',
        object_id=notification.pk,
        object_repr=notification.title,
        reason=f'User {request.user.username} viewed notification: {notification.title}'
    )
    
    return render(request, 'notifications/notification_detail.html', {'notification': notification})

@login_required
def mark_as_read(request, pk):
    """View to mark a notification as read."""
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.mark_as_read()
    
    # Create audit log
    AuditLog.objects.create(
        user=request.user,
        action='update',
        model_name='Notification',
        object_id=notification.pk,
        object_repr=notification.title,
        reason=f'User {request.user.username} marked notification as read: {notification.title}'
    )
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('notifications:notification_list')

@login_required
def mark_all_as_read(request):
    """View to mark all notifications as read."""
    Notification.objects.filter(recipient=request.user, read=False).update(read=True)
    
    # Create audit log
    AuditLog.objects.create(
        user=request.user,
        action='update',
        model_name='Notification',
        object_id=0,
        object_repr='All notifications',
        reason=f'User {request.user.username} marked all notifications as read'
    )
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('notifications:notification_list')

@login_required
def delete_notification(request, pk):
    """View to delete a notification."""
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    
    if request.method == 'POST':
        notification_title = notification.title
        
        # Create audit log
        AuditLog.objects.create(
            user=request.user,
            action='delete',
            model_name='Notification',
            object_id=notification.pk,
            object_repr=notification_title,
            reason=f'User {request.user.username} deleted notification: {notification_title}'
        )
        
        notification.delete()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
        
        return redirect('notifications:notification_list')
    
    return render(request, 'notifications/notification_confirm_delete.html', {'notification': notification})

@login_required
def get_unread_count(request):
    """AJAX view to get the count of unread notifications."""
    count = Notification.objects.filter(recipient=request.user, read=False).count()
    return JsonResponse({'count': count})
