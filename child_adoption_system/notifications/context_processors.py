from .models import Notification

def notification_processor(request):
    """Context processor to add unread notifications to all templates."""
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(
            recipient=request.user,
            read=False
        ).order_by('-created_at')[:5]
        unread_count = unread_notifications.count()
        
        return {
            'unread_notifications': unread_notifications,
            'unread_count': unread_count,
        }
    return {'unread_notifications': [], 'unread_count': 0} 