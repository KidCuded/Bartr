"""
Observer Pattern Implementation for Bartr
Handles event-driven notifications and state changes
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum


class EventType(Enum):
    """Define different types of events in the system"""
    TRADE_CREATED = "trade_created"
    TRADE_ACCEPTED = "trade_accepted"
    TRADE_REJECTED = "trade_rejected"
    TRADE_COMPLETED = "trade_completed"
    ITEM_FLAGGED = "item_flagged"
    ITEM_APPROVED = "item_approved"
    ITEM_DELETED = "item_deleted"
    USER_REGISTERED = "user_registered"
    USER_SUSPENDED = "user_suspended"
    NOTIFICATION_CREATED = "notification_created"
    MESSAGE_SENT = "message_sent"


class Event:
    """Represents an event in the system"""
    
    def __init__(self, event_type: EventType, data: Dict[str, Any], source: str = None):
        self.event_type = event_type
        self.data = data
        self.source = source
        self.timestamp = None
        
    def get_data(self, key: str, default=None):
        """Get specific data from the event"""
        return self.data.get(key, default)


class Observer(ABC):
    """Abstract observer interface"""
    
    @abstractmethod
    def update(self, event: Event) -> None:
        """Handle the event notification"""
        pass
    
    @abstractmethod
    def get_event_types(self) -> List[EventType]:
        """Return list of event types this observer is interested in"""
        pass


class Subject(ABC):
    """Abstract subject interface"""
    
    def __init__(self):
        self._observers: Dict[EventType, List[Observer]] = {}
    
    def attach(self, observer: Observer, event_types: List[EventType] = None) -> None:
        """Attach an observer for specific event types"""
        if event_types is None:
            event_types = observer.get_event_types()
        
        for event_type in event_types:
            if event_type not in self._observers:
                self._observers[event_type] = []
            if observer not in self._observers[event_type]:
                self._observers[event_type].append(observer)
    
    def detach(self, observer: Observer, event_types: List[EventType] = None) -> None:
        """Detach an observer from specific event types"""
        if event_types is None:
            event_types = observer.get_event_types()
        
        for event_type in event_types:
            if event_type in self._observers and observer in self._observers[event_type]:
                self._observers[event_type].remove(observer)
    
    def notify(self, event: Event) -> None:
        """Notify all observers of an event"""
        if event.event_type in self._observers:
            for observer in self._observers[event.event_type]:
                try:
                    observer.update(event)
                except Exception as e:
                    print(f"Error notifying observer {observer.__class__.__name__}: {e}")


class NotificationObserver(Observer):
    """Observer that creates notifications for users"""
    
    def __init__(self):
        from bartr.patterns.builder import NotificationBuilder
        self.notification_builder = NotificationBuilder()
    
    def get_event_types(self) -> List[EventType]:
        return [
            EventType.TRADE_CREATED,
            EventType.TRADE_ACCEPTED,
            EventType.TRADE_REJECTED,
            EventType.ITEM_FLAGGED,
            EventType.ITEM_APPROVED,
            EventType.ITEM_DELETED,
            EventType.USER_SUSPENDED
        ]
    
    def update(self, event: Event) -> None:
        """Create appropriate notifications based on event type"""
        if event.event_type == EventType.TRADE_CREATED:
            self._handle_trade_created(event)
        elif event.event_type == EventType.TRADE_ACCEPTED:
            self._handle_trade_accepted(event)
        elif event.event_type == EventType.TRADE_REJECTED:
            self._handle_trade_rejected(event)
        elif event.event_type == EventType.ITEM_FLAGGED:
            self._handle_item_flagged(event)
        elif event.event_type == EventType.ITEM_APPROVED:
            self._handle_item_approved(event)
        elif event.event_type == EventType.ITEM_DELETED:
            self._handle_item_deleted(event)
        elif event.event_type == EventType.USER_SUSPENDED:
            self._handle_user_suspended(event)
    
    def _handle_trade_created(self, event: Event):
        """Handle trade creation notification"""
        trade_data = event.data
        notification_data = (self.notification_builder
                           .set_type('trade_proposal')
                           .set_content(f"You have received a new trade proposal for {trade_data.get('item_name', 'your item')}")
                           .set_user(trade_data.get('receiver_id'))
                           .set_trade(trade_data.get('trade_id'))
                           .set_priority('high')
                           .set_action_url(f"/trade/{trade_data.get('trade_id')}")
                           .build())
        self._create_notification(notification_data)
    
    def _handle_trade_accepted(self, event: Event):
        """Handle trade acceptance notification"""
        trade_data = event.data
        notification_data = (self.notification_builder
                           .set_type('trade_accepted')
                           .set_content(f"Your trade proposal has been accepted!")
                           .set_user(trade_data.get('sender_id'))
                           .set_trade(trade_data.get('trade_id'))
                           .set_priority('high')
                           .set_action_url(f"/trade/{trade_data.get('trade_id')}")
                           .build())
        self._create_notification(notification_data)
    
    def _handle_trade_rejected(self, event: Event):
        """Handle trade rejection notification"""
        trade_data = event.data
        notification_data = (self.notification_builder
                           .set_type('trade_rejected')
                           .set_content(f"Your trade proposal has been declined.")
                           .set_user(trade_data.get('sender_id'))
                           .set_trade(trade_data.get('trade_id'))
                           .set_priority('medium')
                           .build())
        self._create_notification(notification_data)
    
    def _handle_item_flagged(self, event: Event):
        """Handle item flagging notification"""
        item_data = event.data
        notification_data = (self.notification_builder
                           .set_type('item_flagged')
                           .set_content(f"Your item '{item_data.get('item_name')}' has been reported and is under review.")
                           .set_user(item_data.get('user_id'))
                           .set_item(item_data.get('item_id'))
                           .set_priority('medium')
                           .build())
        self._create_notification(notification_data)
    
    def _handle_item_approved(self, event: Event):
        """Handle item approval notification"""
        item_data = event.data
        notification_data = (self.notification_builder
                           .set_type('item_approved')
                           .set_content(f"Your item '{item_data.get('item_name')}' has been approved and is now visible.")
                           .set_user(item_data.get('user_id'))
                           .set_item(item_data.get('item_id'))
                           .set_priority('low')
                           .build())
        self._create_notification(notification_data)
    
    def _handle_item_deleted(self, event: Event):
        """Handle item deletion notification"""
        item_data = event.data
        notification_data = (self.notification_builder
                           .set_type('item_deleted')
                           .set_content(f"Your item '{item_data.get('item_name')}' has been removed by an administrator.")
                           .set_user(item_data.get('user_id'))
                           .set_item(item_data.get('item_id'))
                           .set_priority('high')
                           .build())
        self._create_notification(notification_data)
    
    def _handle_user_suspended(self, event: Event):
        """Handle user suspension notification"""
        user_data = event.data
        notification_data = (self.notification_builder
                           .set_type('account_suspended')
                           .set_content(f"Your account has been suspended. Please contact support for more information.")
                           .set_user(user_data.get('user_id'))
                           .set_priority('high')
                           .build())
        self._create_notification(notification_data)
    
    def _create_notification(self, notification_data: Dict[str, Any]):
        """Create a notification in the database"""
        try:
            from bartr.models import Notification
            from bartr import db
            
            notification = Notification(
                user_id=notification_data['user_id'],
                type=notification_data['type'],
                content=notification_data['content'],
                item_id=notification_data.get('item_id'),
                trade_id=notification_data.get('trade_id'),
                is_read=notification_data['is_read'],
                created_at=notification_data['created_at']
            )
            
            db.session.add(notification)
            db.session.commit()
        except Exception as e:
            print(f"Error creating notification: {e}")


class EmailObserver(Observer):
    """Observer that sends email notifications for important events"""
    
    def get_event_types(self) -> List[EventType]:
        return [
            EventType.TRADE_ACCEPTED,
            EventType.TRADE_COMPLETED,
            EventType.USER_SUSPENDED,
            EventType.ITEM_DELETED
        ]
    
    def update(self, event: Event) -> None:
        """Send email notifications for critical events"""
        if event.event_type == EventType.TRADE_ACCEPTED:
            self._send_trade_accepted_email(event)
        elif event.event_type == EventType.TRADE_COMPLETED:
            self._send_trade_completed_email(event)
        elif event.event_type == EventType.USER_SUSPENDED:
            self._send_suspension_email(event)
        elif event.event_type == EventType.ITEM_DELETED:
            self._send_item_deleted_email(event)
    
    def _send_trade_accepted_email(self, event: Event):
        """Send email when trade is accepted"""
        trade_data = event.data
        print(f"Email: Trade accepted for user {trade_data.get('sender_id')}")
    
    def _send_trade_completed_email(self, event: Event):
        """Send email when trade is completed"""
        trade_data = event.data
        print(f"Email: Trade completed for users {trade_data.get('participants')}")
    
    def _send_suspension_email(self, event: Event):
        """Send email for account suspension"""
        user_data = event.data
        print(f"Email: Account suspended for user {user_data.get('user_id')}")
    
    def _send_item_deleted_email(self, event: Event):
        """Send email when item is deleted by admin"""
        item_data = event.data
        print(f"Email: Item deleted for user {item_data.get('user_id')}")


class AnalyticsObserver(Observer):
    """Observer that tracks analytics and metrics"""
    
    def get_event_types(self) -> List[EventType]:
        return [
            EventType.TRADE_CREATED,
            EventType.TRADE_COMPLETED,
            EventType.USER_REGISTERED,
            EventType.ITEM_FLAGGED
        ]
    
    def update(self, event: Event) -> None:
        """Track analytics events"""
        if event.event_type == EventType.TRADE_CREATED:
            self._track_trade_created(event)
        elif event.event_type == EventType.TRADE_COMPLETED:
            self._track_trade_completed(event)
        elif event.event_type == EventType.USER_REGISTERED:
            self._track_user_registered(event)
        elif event.event_type == EventType.ITEM_FLAGGED:
            self._track_item_flagged(event)
    
    def _track_trade_created(self, event: Event):
        """Track trade creation metrics"""
        print(f"Analytics: Trade created - {event.data}")
    
    def _track_trade_completed(self, event: Event):
        """Track trade completion metrics"""
        print(f"Analytics: Trade completed - {event.data}")
    
    def _track_user_registered(self, event: Event):
        """Track user registration metrics"""
        print(f"Analytics: User registered - {event.data}")
    
    def _track_item_flagged(self, event: Event):
        """Track item flagging metrics"""
        print(f"Analytics: Item flagged - {event.data}")


class EventManager(Subject):
    """Central event manager for the application"""
    
    def __init__(self):
        super().__init__()
        self._setup_default_observers()
    
    def _setup_default_observers(self):
        """Setup default observers"""
        self.attach(NotificationObserver())
        self.attach(EmailObserver())
        self.attach(AnalyticsObserver())
    
    def emit_event(self, event_type: EventType, data: Dict[str, Any], source: str = None):
        """Emit an event to all interested observers"""
        event = Event(event_type, data, source)
        self.notify(event)
    
    def emit_trade_created(self, trade_id: int, sender_id: int, receiver_id: int, item_name: str):
        """Emit trade created event"""
        self.emit_event(EventType.TRADE_CREATED, {
            'trade_id': trade_id,
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'item_name': item_name
        })
    
    def emit_trade_accepted(self, trade_id: int, sender_id: int, receiver_id: int):
        """Emit trade accepted event"""
        self.emit_event(EventType.TRADE_ACCEPTED, {
            'trade_id': trade_id,
            'sender_id': sender_id,
            'receiver_id': receiver_id
        })
    
    def emit_trade_rejected(self, trade_id: int, sender_id: int, receiver_id: int):
        """Emit trade rejected event"""
        self.emit_event(EventType.TRADE_REJECTED, {
            'trade_id': trade_id,
            'sender_id': sender_id,
            'receiver_id': receiver_id
        })
    
    def emit_item_flagged(self, item_id: int, item_name: str, user_id: int, reporter_id: int, reason: str):
        """Emit item flagged event"""
        self.emit_event(EventType.ITEM_FLAGGED, {
            'item_id': item_id,
            'item_name': item_name,
            'user_id': user_id,
            'reporter_id': reporter_id,
            'reason': reason
        })
    
    def emit_item_deleted(self, item_id: int, item_name: str, user_id: int, admin_id: int):
        """Emit item deleted event"""
        self.emit_event(EventType.ITEM_DELETED, {
            'item_id': item_id,
            'item_name': item_name,
            'user_id': user_id,
            'admin_id': admin_id
        })
    
    def emit_user_suspended(self, user_id: int, admin_id: int, reason: str):
        """Emit user suspended event"""
        self.emit_event(EventType.USER_SUSPENDED, {
            'user_id': user_id,
            'admin_id': admin_id,
            'reason': reason
        })


# Global event manager instance
event_manager = EventManager()