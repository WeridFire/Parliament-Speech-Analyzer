"""
Analyzer Registry - Auto-discovery and management of analyzers.

Provides:
- @analyzer decorator for automatic registration
- AnalyzerRegistry for listing and filtering analyzers
- Dependency resolution for running analyzers in correct order
"""

from typing import Type, Optional
import logging

from .base import BaseAnalyzer

logger = logging.getLogger(__name__)


class AnalyzerRegistry:
    """
    Registry for auto-discovering and managing analyzers.
    
    Usage:
        @analyzer
        class MyAnalyzer(BaseAnalyzer):
            name = "my_analyzer"
            ...
        
        # Get all registered analyzers
        all_analyzers = AnalyzerRegistry.all()
        
        # Get only enabled analyzers
        enabled = AnalyzerRegistry.get_enabled(config)
    """
    
    _analyzers: dict[str, Type[BaseAnalyzer]] = {}
    
    @classmethod
    def register(cls, analyzer_class: Type[BaseAnalyzer]) -> Type[BaseAnalyzer]:
        """
        Register an analyzer class.
        
        Args:
            analyzer_class: The analyzer class to register.
            
        Returns:
            The same class (for use as decorator).
        """
        name = analyzer_class.name
        
        if name in cls._analyzers:
            logger.warning(
                "Overwriting existing analyzer '%s' with %s",
                name, analyzer_class.__name__
            )
        
        cls._analyzers[name] = analyzer_class
        logger.debug("Registered analyzer: %s (%s)", name, analyzer_class.__name__)
        
        return analyzer_class
    
    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseAnalyzer]]:
        """
        Get analyzer class by name.
        
        Args:
            name: The analyzer name (e.g., 'identity', 'sentiment').
            
        Returns:
            Analyzer class or None if not found.
        """
        return cls._analyzers.get(name)
    
    @classmethod
    def all(cls) -> dict[str, Type[BaseAnalyzer]]:
        """
        Get all registered analyzers.
        
        Returns:
            Dict mapping name -> analyzer class.
        """
        return cls._analyzers.copy()
    
    @classmethod
    def names(cls) -> list[str]:
        """
        Get list of all registered analyzer names.
        
        Returns:
            List of analyzer names.
        """
        return list(cls._analyzers.keys())
    
    @classmethod
    def get_enabled(cls, config: dict) -> list[Type[BaseAnalyzer]]:
        """
        Get only enabled analyzers based on config.
        
        Args:
            config: Configuration dict with enabled/disabled flags.
            
        Returns:
            List of enabled analyzer classes.
        """
        enabled = []
        
        for name, analyzer_class in cls._analyzers.items():
            if analyzer_class.is_enabled(config):
                enabled.append(analyzer_class)
            else:
                logger.info("Analyzer '%s' is disabled in config", name)
        
        return enabled
    
    @classmethod
    def get_by_dependency(cls, config: dict) -> list[Type[BaseAnalyzer]]:
        """
        Get enabled analyzers sorted by dependency order.
        
        Analyzers with no dependencies come first.
        
        Args:
            config: Configuration dict.
            
        Returns:
            List of analyzer classes in dependency order.
        """
        enabled = cls.get_enabled(config)
        
        # Simple sorting: analyzers with fewer dependencies first
        def dep_count(a):
            return len(a.get_dependencies())
        
        return sorted(enabled, key=dep_count)
    
    @classmethod
    def clear(cls):
        """Clear all registered analyzers (useful for testing)."""
        cls._analyzers.clear()
        logger.debug("Cleared analyzer registry")


def analyzer(cls: Type[BaseAnalyzer]) -> Type[BaseAnalyzer]:
    """
    Decorator to register an analyzer class.
    
    Usage:
        @analyzer
        class MyAnalyzer(BaseAnalyzer):
            name = "my_analyzer"
            ...
    """
    return AnalyzerRegistry.register(cls)
