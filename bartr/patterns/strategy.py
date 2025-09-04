"""
Strategy Pattern Implementation for Bartr
Handles different algorithms for search, sorting, and recommendations
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import math


class SearchStrategy(ABC):
    """Abstract base class for search strategies"""
    
    @abstractmethod
    def search(self, query: str, items: List[Any], filters: Dict[str, Any] = None) -> List[Any]:
        """Execute the search algorithm"""
        pass
    
    @abstractmethod
    def get_relevance_score(self, item: Any, query: str) -> float:
        """Calculate relevance score for an item"""
        pass


class BasicSearchStrategy(SearchStrategy):
    """Basic text-based search strategy"""
    
    def search(self, query: str, items: List[Any], filters: Dict[str, Any] = None) -> List[Any]:
        """Simple text matching search"""
        if not query:
            return items
        
        query_terms = query.lower().split()
        scored_items = []
        
        for item in items:
            score = self.get_relevance_score(item, query)
            if score > 0:
                scored_items.append((item, score))
        
        # Sort by relevance score (descending)
        scored_items.sort(key=lambda x: x[1], reverse=True)
        return [item for item, score in scored_items]
    
    def get_relevance_score(self, item: Any, query: str) -> float:
        """Calculate basic relevance score"""
        query_terms = query.lower().split()
        item_text = f"{item.name} {item.description}".lower()
        
        score = 0
        for term in query_terms:
            if term in item.name.lower():
                score += 3  # Higher weight for name matches
            elif term in item.description.lower():
                score += 1  # Lower weight for description matches
        
        return score


class FuzzySearchStrategy(SearchStrategy):
    """Fuzzy search strategy with approximate matching"""
    
    def search(self, query: str, items: List[Any], filters: Dict[str, Any] = None) -> List[Any]:
        """Fuzzy matching search with typo tolerance"""
        if not query:
            return items
        
        scored_items = []
        
        for item in items:
            score = self.get_relevance_score(item, query)
            if score > 0.3:  # Minimum fuzzy match threshold
                scored_items.append((item, score))
        
        scored_items.sort(key=lambda x: x[1], reverse=True)
        return [item for item, score in scored_items]
    
    def get_relevance_score(self, item: Any, query: str) -> float:
        """Calculate fuzzy relevance score using Levenshtein distance"""
        query_lower = query.lower()
        item_text = f"{item.name} {item.description}".lower()
        
        # Check for exact matches first
        if query_lower in item_text:
            return 1.0
        
        # Calculate fuzzy match scores
        name_score = self._fuzzy_match(query_lower, item.name.lower())
        desc_score = self._fuzzy_match(query_lower, item.description.lower()) * 0.5
        
        return max(name_score, desc_score)
    
    def _fuzzy_match(self, query: str, text: str) -> float:
        """Calculate fuzzy match score using simple similarity"""
        if not query or not text:
            return 0
        
        # Simple character overlap ratio
        query_chars = set(query)
        text_chars = set(text)
        overlap = len(query_chars.intersection(text_chars))
        union = len(query_chars.union(text_chars))
        
        return overlap / union if union > 0 else 0


class SemanticSearchStrategy(SearchStrategy):
    """Semantic search strategy using keyword associations"""
    
    def __init__(self):
        # Simple keyword associations for semantic search
        self.synonyms = {
            'phone': ['mobile', 'smartphone', 'cell', 'iphone', 'android'],
            'car': ['vehicle', 'auto', 'automobile', 'truck', 'suv'],
            'book': ['novel', 'textbook', 'manual', 'guide', 'literature'],
            'computer': ['pc', 'laptop', 'desktop', 'mac', 'workstation'],
            'game': ['gaming', 'video game', 'console', 'nintendo', 'playstation']
        }
    
    def search(self, query: str, items: List[Any], filters: Dict[str, Any] = None) -> List[Any]:
        """Semantic search with synonym expansion"""
        if not query:
            return items
        
        # Expand query with synonyms
        expanded_terms = self._expand_query(query)
        
        scored_items = []
        for item in items:
            score = self.get_relevance_score(item, query, expanded_terms)
            if score > 0:
                scored_items.append((item, score))
        
        scored_items.sort(key=lambda x: x[1], reverse=True)
        return [item for item, score in scored_items]
    
    def get_relevance_score(self, item: Any, query: str, expanded_terms: List[str] = None) -> float:
        """Calculate semantic relevance score"""
        if expanded_terms is None:
            expanded_terms = self._expand_query(query)
        
        item_text = f"{item.name} {item.description}".lower()
        score = 0
        
        for term in expanded_terms:
            if term in item_text:
                # Original query terms get higher weight
                weight = 2.0 if term in query.lower() else 1.0
                score += weight
        
        return score
    
    def _expand_query(self, query: str) -> List[str]:
        """Expand query with synonyms"""
        terms = query.lower().split()
        expanded = terms.copy()
        
        for term in terms:
            for key, synonyms in self.synonyms.items():
                if term in synonyms or term == key:
                    expanded.extend([key] + synonyms)
        
        return list(set(expanded))  # Remove duplicates


class SortingStrategy(ABC):
    """Abstract base class for sorting strategies"""
    
    @abstractmethod
    def sort(self, items: List[Any], reverse: bool = False) -> List[Any]:
        """Sort items according to the strategy"""
        pass


class DateSortStrategy(SortingStrategy):
    """Sort by creation date"""
    
    def sort(self, items: List[Any], reverse: bool = False) -> List[Any]:
        return sorted(items, key=lambda x: x.created_at, reverse=reverse)


class PriceSortStrategy(SortingStrategy):
    """Sort by estimated value/price"""
    
    def sort(self, items: List[Any], reverse: bool = False) -> List[Any]:
        return sorted(items, key=lambda x: x.estimated_value or 0, reverse=reverse)


class PopularitySortStrategy(SortingStrategy):
    """Sort by popularity (views, trades, etc.)"""
    
    def sort(self, items: List[Any], reverse: bool = False) -> List[Any]:
        def popularity_score(item):
            # Calculate popularity based on views and trade proposals
            views = getattr(item, 'views', 0)
            proposals = len(getattr(item, 'trade_proposals', []))
            return views * 0.7 + proposals * 0.3
        
        return sorted(items, key=popularity_score, reverse=reverse)


class ConditionSortStrategy(SortingStrategy):
    """Sort by item condition"""
    
    def __init__(self):
        self.condition_order = {
            'New': 5,
            'Like New': 4,
            'Good': 3,
            'Fair': 2,
            'Poor': 1
        }
    
    def sort(self, items: List[Any], reverse: bool = False) -> List[Any]:
        return sorted(items, 
                     key=lambda x: self.condition_order.get(x.condition, 0), 
                     reverse=reverse)


class RecommendationStrategy(ABC):
    """Abstract base class for recommendation strategies"""
    
    @abstractmethod
    def get_recommendations(self, user_id: int, items: List[Any], limit: int = 10) -> List[Any]:
        """Get recommended items for a user"""
        pass


class CollaborativeFilteringStrategy(RecommendationStrategy):
    """Collaborative filtering recommendation strategy"""
    
    def get_recommendations(self, user_id: int, items: List[Any], limit: int = 10) -> List[Any]:
        """Recommend items based on similar users' preferences"""
        try:
            from bartr.models import User, TradeProposal, Item
            
            # Find users with similar trade patterns
            user = User.query.get(user_id)
            if not user:
                return []
            
            # Get user's trade categories
            user_categories = self._get_user_categories(user_id)
            if not user_categories:
                return items[:limit]  # Return recent items if no history
            
            # Score items based on category preferences
            scored_items = []
            for item in items:
                if item.user_id != user_id and item.is_active:
                    score = self._calculate_collaborative_score(item, user_categories)
                    if score > 0:
                        scored_items.append((item, score))
            
            scored_items.sort(key=lambda x: x[1], reverse=True)
            return [item for item, score in scored_items[:limit]]
        
        except Exception:
            return items[:limit]
    
    def _get_user_categories(self, user_id: int) -> Dict[int, float]:
        """Get user's category preferences based on trade history"""
        try:
            from bartr.models import TradeProposal, Item
            
            # Get user's accepted trades
            proposals = TradeProposal.query.filter_by(
                sender_id=user_id, 
                status='accepted'
            ).all()
            
            category_scores = {}
            for proposal in proposals:
                item = Item.query.get(proposal.requested_item_id)
                if item and item.category_id:
                    category_scores[item.category_id] = category_scores.get(item.category_id, 0) + 1
            
            # Normalize scores
            total = sum(category_scores.values())
            if total > 0:
                for cat_id in category_scores:
                    category_scores[cat_id] /= total
            
            return category_scores
        except Exception:
            return {}
    
    def _calculate_collaborative_score(self, item: Any, user_categories: Dict[int, float]) -> float:
        """Calculate collaborative filtering score"""
        if item.category_id in user_categories:
            return user_categories[item.category_id]
        return 0


class ContentBasedStrategy(RecommendationStrategy):
    """Content-based recommendation strategy"""
    
    def get_recommendations(self, user_id: int, items: List[Any], limit: int = 10) -> List[Any]:
        """Recommend items based on user's item characteristics"""
        try:
            from bartr.models import User, Item
            
            user = User.query.get(user_id)
            if not user:
                return []
            
            # Get user's items to understand preferences
            user_items = Item.query.filter_by(user_id=user_id, is_active=True).all()
            if not user_items:
                return items[:limit]
            
            # Calculate content similarity
            scored_items = []
            for item in items:
                if item.user_id != user_id and item.is_active:
                    score = self._calculate_content_similarity(item, user_items)
                    if score > 0:
                        scored_items.append((item, score))
            
            scored_items.sort(key=lambda x: x[1], reverse=True)
            return [item for item, score in scored_items[:limit]]
        
        except Exception:
            return items[:limit]
    
    def _calculate_content_similarity(self, item: Any, user_items: List[Any]) -> float:
        """Calculate content-based similarity score"""
        max_score = 0
        
        for user_item in user_items:
            score = 0
            
            # Category similarity
            if item.category_id == user_item.category_id:
                score += 0.5
            
            # Condition similarity
            if item.condition == user_item.condition:
                score += 0.2
            
            # Price range similarity
            if (item.estimated_value and user_item.estimated_value and
                abs(item.estimated_value - user_item.estimated_value) < 50):
                score += 0.3
            
            max_score = max(max_score, score)
        
        return max_score


class HybridRecommendationStrategy(RecommendationStrategy):
    """Hybrid recommendation combining multiple strategies"""
    
    def __init__(self):
        self.collaborative = CollaborativeFilteringStrategy()
        self.content_based = ContentBasedStrategy()
    
    def get_recommendations(self, user_id: int, items: List[Any], limit: int = 10) -> List[Any]:
        """Combine collaborative and content-based recommendations"""
        # Get recommendations from both strategies
        collab_recs = self.collaborative.get_recommendations(user_id, items, limit * 2)
        content_recs = self.content_based.get_recommendations(user_id, items, limit * 2)
        
        # Combine and score
        item_scores = {}
        
        # Weight collaborative filtering
        for i, item in enumerate(collab_recs):
            score = (len(collab_recs) - i) / len(collab_recs) * 0.6
            item_scores[item.id] = item_scores.get(item.id, 0) + score
        
        # Weight content-based
        for i, item in enumerate(content_recs):
            score = (len(content_recs) - i) / len(content_recs) * 0.4
            item_scores[item.id] = item_scores.get(item.id, 0) + score
        
        # Sort by combined score
        all_items = {item.id: item for item in collab_recs + content_recs}
        sorted_items = sorted(item_scores.items(), key=lambda x: x[1], reverse=True)
        
        result = []
        for item_id, score in sorted_items[:limit]:
            if item_id in all_items:
                result.append(all_items[item_id])
        
        return result


class AlgorithmContext:
    """Context class that uses different algorithm strategies"""
    
    def __init__(self):
        self.search_strategy: SearchStrategy = BasicSearchStrategy()
        self.sort_strategy: SortingStrategy = DateSortStrategy()
        self.recommendation_strategy: RecommendationStrategy = HybridRecommendationStrategy()
    
    def set_search_strategy(self, strategy: SearchStrategy):
        """Set the search strategy"""
        self.search_strategy = strategy
    
    def set_sort_strategy(self, strategy: SortingStrategy):
        """Set the sorting strategy"""
        self.sort_strategy = strategy
    
    def set_recommendation_strategy(self, strategy: RecommendationStrategy):
        """Set the recommendation strategy"""
        self.recommendation_strategy = strategy
    
    def search_items(self, query: str, items: List[Any], filters: Dict[str, Any] = None) -> List[Any]:
        """Search items using current strategy"""
        return self.search_strategy.search(query, items, filters)
    
    def sort_items(self, items: List[Any], reverse: bool = False) -> List[Any]:
        """Sort items using current strategy"""
        return self.sort_strategy.sort(items, reverse)
    
    def get_recommendations(self, user_id: int, items: List[Any], limit: int = 10) -> List[Any]:
        """Get recommendations using current strategy"""
        return self.recommendation_strategy.get_recommendations(user_id, items, limit)


# Strategy factory for easy strategy selection
class StrategyFactory:
    """Factory for creating algorithm strategies"""
    
    @staticmethod
    def create_search_strategy(strategy_type: str) -> SearchStrategy:
        """Create a search strategy by type"""
        strategies = {
            'basic': BasicSearchStrategy,
            'fuzzy': FuzzySearchStrategy,
            'semantic': SemanticSearchStrategy
        }
        
        strategy_class = strategies.get(strategy_type.lower(), BasicSearchStrategy)
        return strategy_class()
    
    @staticmethod
    def create_sort_strategy(strategy_type: str) -> SortingStrategy:
        """Create a sorting strategy by type"""
        strategies = {
            'date': DateSortStrategy,
            'price': PriceSortStrategy,
            'popularity': PopularitySortStrategy,
            'condition': ConditionSortStrategy
        }
        
        strategy_class = strategies.get(strategy_type.lower(), DateSortStrategy)
        return strategy_class()
    
    @staticmethod
    def create_recommendation_strategy(strategy_type: str) -> RecommendationStrategy:
        """Create a recommendation strategy by type"""
        strategies = {
            'collaborative': CollaborativeFilteringStrategy,
            'content': ContentBasedStrategy,
            'hybrid': HybridRecommendationStrategy
        }
        
        strategy_class = strategies.get(strategy_type.lower(), HybridRecommendationStrategy)
        return strategy_class()