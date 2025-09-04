# Design Patterns Implementation for Bartr

from .builder import NotificationBuilder, TradeProposalBuilder, SearchQueryBuilder
from .observer import (
    EventType, Event, Observer, Subject, NotificationObserver, 
    EmailObserver, AnalyticsObserver, EventManager, event_manager
)
from .strategy import (
    SearchStrategy, BasicSearchStrategy, FuzzySearchStrategy, SemanticSearchStrategy,
    SortingStrategy, DateSortStrategy, PriceSortStrategy, PopularitySortStrategy, ConditionSortStrategy,
    RecommendationStrategy, CollaborativeFilteringStrategy, ContentBasedStrategy, HybridRecommendationStrategy,
    AlgorithmContext, StrategyFactory
)
from .singleton import (
    ConfigManager, CacheManager, DatabaseManager, NotificationManager, SessionManager,
    get_config, get_cache, get_database, get_notifications, get_sessions
)
from .command import (
    Command, CommandStatus, SuspendUserCommand, DeleteItemCommand, CreateBackupCommand,
    BatchCommand, MacroCommand, CommandInvoker, CommandQueue, command_invoker, command_queue
)

__all__ = [
    # Builder Pattern
    'NotificationBuilder', 'TradeProposalBuilder', 'SearchQueryBuilder',
    
    # Observer Pattern
    'EventType', 'Event', 'Observer', 'Subject', 'NotificationObserver', 
    'EmailObserver', 'AnalyticsObserver', 'EventManager', 'event_manager',
    
    # Strategy Pattern
    'SearchStrategy', 'BasicSearchStrategy', 'FuzzySearchStrategy', 'SemanticSearchStrategy',
    'SortingStrategy', 'DateSortStrategy', 'PriceSortStrategy', 'PopularitySortStrategy', 'ConditionSortStrategy',
    'RecommendationStrategy', 'CollaborativeFilteringStrategy', 'ContentBasedStrategy', 'HybridRecommendationStrategy',
    'AlgorithmContext', 'StrategyFactory',
    
    # Singleton Pattern
    'ConfigManager', 'CacheManager', 'DatabaseManager', 'NotificationManager', 'SessionManager',
    'get_config', 'get_cache', 'get_database', 'get_notifications', 'get_sessions',
    
    # Command Pattern
    'Command', 'CommandStatus', 'SuspendUserCommand', 'DeleteItemCommand', 'CreateBackupCommand',
    'BatchCommand', 'MacroCommand', 'CommandInvoker', 'CommandQueue', 'command_invoker', 'command_queue'
]