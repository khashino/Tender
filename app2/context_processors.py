from .models import Notification, Message, App2User
from .auth_backend import OracleUser

def notifications_and_messages(request):
    notification_count = 0
    message_count = 0
    notifications = []
    messages = []
    
    if request.user.is_authenticated:
        # Notifications are system-wide, so we can show them to all authenticated users
        notification_count = Notification.objects.filter(is_active=True).count()
        notifications = Notification.objects.filter(is_active=True).order_by('-created_at')[:5]
        
        # Messages are only for App2 users (not Oracle users)
        if isinstance(request.user, App2User):
            message_count = Message.objects.filter(receiver=request.user, is_read=False).count()
            messages = Message.objects.filter(receiver=request.user).order_by('-created_at')[:5]
        # For Oracle users, we don't have messages yet
        elif isinstance(request.user, OracleUser):
            message_count = 0
            messages = []
    
    return {
        'notification_count': notification_count,
        'message_count': message_count,
        'notifications': notifications,
        'messages': messages,
    } 