"""
Logging configuration and LangSmith hooks.
"""

import logging
import os
from pathlib import Path
from typing import Optional, Dict

# Global file handlers for DEBUG mode
_file_handlers: Dict[str, logging.FileHandler] = {}

def setup_logging(level=logging.INFO, config=None, log_dir: Optional[str] = None):
    """
    Configure standard logging and enable LangSmith tracing if LANGSMITH mode.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR) - controls console output only
        config: Optional Config object to check for LangSmith project name
        log_dir: Directory for component log files (always enabled if provided)
    """
    # Force reconfiguration for Jupyter notebooks
    logging.basicConfig(
        level=level, 
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=True  # Python 3.8+: force reconfiguration
    )
    
    # Explicitly set root logger level (needed for Jupyter)
    logging.getLogger().setLevel(level)
    
    # Also set level for all existing handlers (console handlers)
    for handler in logging.getLogger().handlers:
        handler.setLevel(level)
    
    # Check log_level string from config to determine mode
    log_level_str = None
    if config and hasattr(config, 'log_level'):
        log_level_str = config.log_level.upper()
    
    # Enable LangSmith tracing when log_level is LANGSMITH
    if log_level_str == "LANGSMITH":
        # Set environment variables for LangSmith if not already set
        if os.getenv("LANGCHAIN_TRACING_V2") is None:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            logging.info("LangSmith tracing enabled (LANGSMITH mode)")
        
        # Set project name if config provided
        if config and hasattr(config, 'langsmith_project'):
            if os.getenv("LANGCHAIN_PROJECT") is None:
                os.environ["LANGCHAIN_PROJECT"] = config.langsmith_project
            logging.info(f"LangSmith project set to: {config.langsmith_project}")
        else:
            # Use default if no config
            if os.getenv("LANGCHAIN_PROJECT") is None:
                os.environ["LANGCHAIN_PROJECT"] = "oracle-classification"
            logging.info(f"LangSmith project set to: {os.getenv('LANGCHAIN_PROJECT')}")
        
        # Check if API key is set
        if os.getenv("LANGCHAIN_API_KEY") is None:
            if config and hasattr(config, 'langsmith_api_key') and config.langsmith_api_key:
                os.environ["LANGCHAIN_API_KEY"] = config.langsmith_api_key
                logging.info("LangSmith API key set from config")
            else:
                logging.warning(
                    "LANGCHAIN_API_KEY not set. LangSmith tracing will not work. "
                    "Set LANGCHAIN_API_KEY environment variable to enable tracing."
                )
        else:
            logging.info("LangSmith API key found - tracing will be sent to LangSmith")
    
    # Setup file logging - always enabled if log_dir is provided
    # File handlers will always log at DEBUG level regardless of console log level
    if log_dir:
        setup_component_file_logging(log_dir)

def setup_component_file_logging(log_dir: str):
    """
    Setup separate log files for extractor, traversal, and verifier.
    These files always log at DEBUG level regardless of console log level.
    
    Args:
        log_dir: Directory where log files will be created
    """
    global _file_handlers
    
    # Create log directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Components to create log files for
    components = {
        "extractor": "oracle.extract.concept_extractor",
        "traversal": "oracle.match.traversal",
        "verifier": "oracle.verify.verifier",
        "ontology_loader": "oracle.data.ontology_loader"
    }
    
    for component_name, logger_name in components.items():
        log_file = log_path / f"{component_name}.log"
        
        # Remove existing handler if any
        if component_name in _file_handlers:
            component_logger = logging.getLogger(logger_name)
            component_logger.removeHandler(_file_handlers[component_name])
            _file_handlers[component_name].close()
        
        # Create file handler - always at DEBUG level to capture everything
        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')  # Overwrite existing file
        file_handler.setLevel(logging.DEBUG)  # Always DEBUG to capture all messages
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        
        # Add handler to component logger
        component_logger = logging.getLogger(logger_name)
        component_logger.addHandler(file_handler)
        # Set logger to DEBUG so it passes all messages to the file handler
        # Keep propagate=True so messages also go to console (filtered by console log level)
        component_logger.setLevel(logging.DEBUG)
        
        # Store handler for cleanup
        _file_handlers[component_name] = file_handler
        
        # Only log this if we're in a mode that would show it
        root_logger = logging.getLogger()
        if root_logger.level <= logging.INFO:
            logging.info(f"Component logging enabled for {component_name}: {log_file} (always DEBUG level)")

def cleanup_file_handlers():
    """Close and remove all file handlers."""
    global _file_handlers
    for handler in _file_handlers.values():
        handler.close()
    _file_handlers.clear()
