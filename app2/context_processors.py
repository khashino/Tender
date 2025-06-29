from .models import Notification, Message, App2User
from .auth_backend import OracleUser
from .oracle_utils import (
    get_oracle_user_messages, 
    get_oracle_user_message_count,
    get_oracle_notifications,
    get_oracle_notification_count
)

def notifications_and_messages(request):
    notification_count = 0
    message_count = 0
    notifications = []
    messages = []
    
    if request.user.is_authenticated:
        if isinstance(request.user, OracleUser):
            # For Oracle users, get data from Oracle tables
            try:
                # Get user's group_id for notifications
                user_group_id = getattr(request.user, 'group_id', None)
                
                # Get notifications from Oracle (either by group or all)
                oracle_notifications = get_oracle_notifications(group_id=user_group_id, limit=5)
                notification_count = get_oracle_notification_count(group_id=user_group_id)
                
                # Convert Oracle notifications to template-friendly format
                notifications = []
                for notif in oracle_notifications:
                    notifications.append({
                        'id': notif.get('NOTIF_ID'),
                        'title': notif.get('TYPE', 'اعلان'),  # Use TYPE as title or default
                        'message': notif.get('NOTIF_TEXT', ''),
                        'notification_type': 'info',  # Default type
                        'created_at': notif.get('NOTIF_DATE'),
                    })
                
                # Get messages from Oracle
                user_id = getattr(request.user, 'user_id', None)
                if user_id:
                    oracle_messages = get_oracle_user_messages(user_id, limit=5)
                    message_count = get_oracle_user_message_count(user_id, unread_only=True)
                    
                    # Convert Oracle messages to template-friendly format
                    messages = []
                    for msg in oracle_messages:
                        messages.append({
                            'id': msg.get('MESSAGE_ID'),
                            'subject': msg.get('TYPE', 'پیام'),  # Use TYPE as subject or default
                            'content': msg.get('MESSAGE_TEXT', ''),
                            'created_at': msg.get('SENT_DATE'),
                            'is_read': msg.get('IS_READ', 0) == 1,
                        })
                
            except Exception as e:
                # Log error but don't break the page
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error loading Oracle notifications/messages: {str(e)}")
                
        elif isinstance(request.user, App2User):
            # For Django App2 users, use Django models
            # Notifications are system-wide, so we can show them to all authenticated users
            notification_count = Notification.objects.filter(is_active=True).count()
            notifications = Notification.objects.filter(is_active=True).order_by('-created_at')[:5]
            
            # Messages are only for App2 users
            message_count = Message.objects.filter(receiver=request.user, is_read=False).count()
            messages = Message.objects.filter(receiver=request.user).order_by('-created_at')[:5]
    
    return {
        'notification_count': notification_count,
        'message_count': message_count,
        'notifications': notifications,
        'messages': messages,
    } 