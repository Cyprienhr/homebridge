from .models import Notification

def notification_processor(request):
    """Context processor to add unread notifications to all templates."""
    if request.user.is_authenticated:
        # Get unread notifications
        unread_notifications = Notification.objects.filter(
            recipient=request.user,
            read=False
        ).order_by('-created_at')
        
        # Get recent notifications (both read and unread)
        recent_notifications = Notification.objects.filter(
            recipient=request.user
        ).order_by('-created_at')[:5]
        
        # Total counts
        unread_count = unread_notifications.count()
        total_count = Notification.objects.filter(recipient=request.user).count()
        
        return {
            'unread_notifications': unread_notifications[:5],  # Limit to 5 for dropdown
            'recent_notifications': recent_notifications,
            'notifications_count': unread_count,
            'total_notifications_count': total_count,
        }
    return {
        'unread_notifications': [],
        'recent_notifications': [],
        'notifications_count': 0,
        'total_notifications_count': 0
    } 