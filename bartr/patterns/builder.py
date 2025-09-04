"""
Builder Pattern Implementation for Bartr
Handles complex object creation with multiple configuration options
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, Any
from bartr.models import malaysia_now


class NotificationBuilder:
    """Builder for creating complex notification objects"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset the builder to create a new notification"""
        self._notification_data = {
            'type': None,
            'content': None,
            'user_id': None,
            'item_id': None,
            'trade_id': None,
            'is_read': False,
            'created_at': malaysia_now(),
            'metadata': {}
        }
        return self
    
    def set_type(self, notification_type: str):
        """Set the notification type"""
        self._notification_data['type'] = notification_type
        return self
    
    def set_content(self, content: str):
        """Set the notification content"""
        self._notification_data['content'] = content
        return self
    
    def set_user(self, user_id: int):
        """Set the target user for the notification"""
        self._notification_data['user_id'] = user_id
        return self
    
    def set_item(self, item_id: int):
        """Set the related item for the notification"""
        self._notification_data['item_id'] = item_id
        return self
    
    def set_trade(self, trade_id: int):
        """Set the related trade for the notification"""
        self._notification_data['trade_id'] = trade_id
        return self
    
    def add_metadata(self, key: str, value: Any):
        """Add metadata to the notification"""
        self._notification_data['metadata'][key] = value
        return self
    
    def set_priority(self, priority: str):
        """Set notification priority (high, medium, low)"""
        return self.add_metadata('priority', priority)
    
    def set_action_url(self, url: str):
        """Set action URL for the notification"""
        return self.add_metadata('action_url', url)
    
    def build(self) -> Dict[str, Any]:
        """Build and return the notification data"""
        if not self._notification_data['type'] or not self._notification_data['content']:
            raise ValueError("Notification type and content are required")
        
        result = self._notification_data.copy()
        self.reset()  # Reset for next build
        return result


class TradeProposalBuilder:
    """Builder for creating complex trade proposals"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset the builder to create a new trade proposal"""
        self._trade_data = {
            'sender_id': None,
            'receiver_id': None,
            'requested_item_id': None,
            'offered_items': [],
            'message': '',
            'status': 'pending',
            'created_at': malaysia_now(),
            'fairness_threshold': 50,  # Minimum fairness score to accept
            'auto_reject_unfair': False,
            'expires_at': None
        }
        return self
    
    def set_sender(self, sender_id: int):
        """Set the trade sender"""
        self._trade_data['sender_id'] = sender_id
        return self
    
    def set_receiver(self, receiver_id: int):
        """Set the trade receiver"""
        self._trade_data['receiver_id'] = receiver_id
        return self
    
    def set_requested_item(self, item_id: int):
        """Set the item being requested"""
        self._trade_data['requested_item_id'] = item_id
        return self
    
    def add_offered_item(self, item_id: int):
        """Add an item to the offer"""
        if item_id not in self._trade_data['offered_items']:
            self._trade_data['offered_items'].append(item_id)
        return self
    
    def set_message(self, message: str):
        """Set the trade proposal message"""
        self._trade_data['message'] = message
        return self
    
    def set_fairness_threshold(self, threshold: int):
        """Set minimum fairness score required"""
        self._trade_data['fairness_threshold'] = max(0, min(100, threshold))
        return self
    
    def enable_auto_reject_unfair(self):
        """Enable automatic rejection of unfair trades"""
        self._trade_data['auto_reject_unfair'] = True
        return self
    
    def set_expiration(self, expires_at: datetime):
        """Set trade proposal expiration"""
        self._trade_data['expires_at'] = expires_at
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build and return the trade proposal data"""
        required_fields = ['sender_id', 'receiver_id', 'requested_item_id']
        for field in required_fields:
            if self._trade_data[field] is None:
                raise ValueError(f"Trade proposal requires {field}")
        
        if not self._trade_data['offered_items']:
            raise ValueError("Trade proposal must include at least one offered item")
        
        result = self._trade_data.copy()
        self.reset()  # Reset for next build
        return result


class SearchQueryBuilder:
    """Builder for creating complex search queries"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset the builder for a new search query"""
        self._query_data = {
            'text': '',
            'category_id': None,
            'condition': None,
            'min_price': None,
            'max_price': None,
            'location': {'state': None, 'city': None},
            'sort_by': 'created_at',
            'sort_order': 'desc',
            'page': 1,
            'per_page': 20,
            'filters': {},
            'exclude_user_items': False,
            'only_active': True
        }
        return self
    
    def set_text(self, text: str):
        """Set search text"""
        self._query_data['text'] = text.strip()
        return self
    
    def set_category(self, category_id: int):
        """Set category filter"""
        self._query_data['category_id'] = category_id
        return self
    
    def set_condition(self, condition: str):
        """Set item condition filter"""
        self._query_data['condition'] = condition
        return self
    
    def set_price_range(self, min_price: float = None, max_price: float = None):
        """Set price range filter"""
        if min_price is not None:
            self._query_data['min_price'] = max(0, min_price)
        if max_price is not None:
            self._query_data['max_price'] = max(0, max_price)
        return self
    
    def set_location(self, state: str = None, city: str = None):
        """Set location filter"""
        if state:
            self._query_data['location']['state'] = state
        if city:
            self._query_data['location']['city'] = city
        return self
    
    def set_sorting(self, sort_by: str, sort_order: str = 'desc'):
        """Set sorting criteria"""
        valid_sort_fields = ['created_at', 'name', 'estimated_value', 'condition']
        valid_orders = ['asc', 'desc']
        
        if sort_by in valid_sort_fields:
            self._query_data['sort_by'] = sort_by
        if sort_order in valid_orders:
            self._query_data['sort_order'] = sort_order
        return self
    
    def set_pagination(self, page: int, per_page: int = 20):
        """Set pagination parameters"""
        self._query_data['page'] = max(1, page)
        self._query_data['per_page'] = max(1, min(100, per_page))
        return self
    
    def exclude_user_items(self, user_id: int):
        """Exclude items from specific user"""
        self._query_data['exclude_user_items'] = user_id
        return self
    
    def include_inactive(self):
        """Include inactive items in search"""
        self._query_data['only_active'] = False
        return self
    
    def add_custom_filter(self, key: str, value: Any):
        """Add custom filter"""
        self._query_data['filters'][key] = value
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build and return the search query"""
        result = self._query_data.copy()
        self.reset()  # Reset for next build
        return result