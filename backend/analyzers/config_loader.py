"""
Configuration Loader - Load and manage analyzer configuration.

Provides:
- YAML config loading
- Default values
- Validation
- Runtime overrides
"""

import logging
from pathlib import Path
from typing import Optional, Any

logger = logging.getLogger(__name__)

# Try to import yaml, provide fallback
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    logger.warning("PyYAML not installed. Using default configuration.")


# Default configuration (used if YAML not available or file missing)
DEFAULT_CONFIG = {
    'identity': {
        'enabled': True,
        'features': {
            'thematic_fingerprint': True,
            'generalism_index': True,
            'distinctive_keywords': True,
        }
    },
    'sentiment': {
        'enabled': True,
        'use_transformer': False,
        'features': {
            'topic_sentiment': True,
            'readability': True,
            'polarization': True,
            'party_topic_sentiment': True,
            'sentiment_rankings': True,
        }
    },
    'temporal': {
        'enabled': True,
        'granularity': 'month',
        'features': {
            'topic_trends': True,
            'semantic_drift': True,
            'crisis_index': True,
            'topic_surfing': True,
        }
    },
    'relations': {
        'enabled': True,
        'features': {
            'affinity_matrix': True,
            'party_cohesion': True,
            'thematic_overlap': True,
            'cross_party_pairs': True,
        }
    },
    'speaker': {
        'enabled': True,
        'features': {
            'verbosity': True,
            'linguistic': True,
            'consistency': True,
            'topic_leadership': True,
            'intervention_patterns': True,
            'vocabulary': True,
            'network': True,
            'entity_focus': False,
        }
    },
    'rhetoric': {
        'enabled': True,
        'features': {
            'populist': True,
            'anti_establishment': True,
            'emotional': True,
            'institutional': True,
        }
    },
    'factions': {
        'enabled': True,
        'features': {
            'conformity': True,
            'faction_detection': True,
        }
    },
    'alliances': {
        'enabled': True,
        'features': {
            'transversal_clusters': True,
            'unusual_pairs': True,
            'left_right_alliances': True,
        }
    },
    'topics': {
        'enabled': True,
        'use_pos_filtering': True,
        'top_n_keywords': 5,
    }
}


def load_config(config_path: Optional[Path] = None) -> dict:
    """
    Load analyzer configuration from YAML file.
    
    Args:
        config_path: Path to YAML config file. If None, uses default location.
        
    Returns:
        Configuration dictionary.
    """
    # Default path
    if config_path is None:
        config_path = Path(__file__).parent / 'config.yaml'
    else:
        config_path = Path(config_path)
    
    # Start with defaults
    config = deep_copy_config(DEFAULT_CONFIG)
    
    # Load from file if available
    if YAML_AVAILABLE and config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f) or {}
            
            # Merge file config into defaults
            config = deep_merge(config, file_config)
            logger.info("Loaded config from %s", config_path)
            
        except Exception as e:
            logger.warning("Failed to load config from %s: %s", config_path, e)
    else:
        logger.info("Using default configuration")
    
    return config


def deep_copy_config(config: dict) -> dict:
    """Create a deep copy of config dict."""
    result = {}
    for key, value in config.items():
        if isinstance(value, dict):
            result[key] = deep_copy_config(value)
        else:
            result[key] = value
    return result


def deep_merge(base: dict, override: dict) -> dict:
    """
    Deep merge override into base config.
    
    Args:
        base: Base configuration dict.
        override: Override values to apply.
        
    Returns:
        Merged configuration.
    """
    result = deep_copy_config(base)
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def get_analyzer_config(config: dict, analyzer_name: str) -> dict:
    """
    Get configuration for a specific analyzer.
    
    Args:
        config: Full configuration dict.
        analyzer_name: Name of the analyzer.
        
    Returns:
        Analyzer-specific configuration.
    """
    return config.get(analyzer_name, {'enabled': True, 'features': {}})


def is_feature_enabled(config: dict, analyzer_name: str, feature_name: str) -> bool:
    """
    Check if a specific feature is enabled.
    
    Args:
        config: Full configuration dict.
        analyzer_name: Name of the analyzer.
        feature_name: Name of the feature.
        
    Returns:
        True if feature is enabled.
    """
    analyzer_config = get_analyzer_config(config, analyzer_name)
    
    if not analyzer_config.get('enabled', True):
        return False
    
    features = analyzer_config.get('features', {})
    return features.get(feature_name, True)


def save_config(config: dict, config_path: Path):
    """
    Save configuration to YAML file.
    
    Args:
        config: Configuration dict.
        config_path: Path to save to.
    """
    if not YAML_AVAILABLE:
        raise ImportError("PyYAML required to save config")
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(config, f, default_flow_style=False, allow_unicode=True)
    
    logger.info("Saved config to %s", config_path)
