import logging
from .server.server import mcp
from pathlib import Path
import os, sys
import logging.config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define and apply your custom logging configuration
logging_config = {
    'version': 1,
    # Crucially, this prevents your config from wiping out existing loggers.
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': 'INFO',
        },
    },
    'loggers': {
        '': {  # This is the root logger
            'handlers': ['console'],
            'level': 'INFO',
        },
        'uvicorn': {  # Customize uvicorn logs to be less verbose
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        }
    },
}

logging.config.dictConfig(logging_config)

# Now, retrieve and use your custom logger
logger = logging.getLogger("my_custom_app")
logger.info("This is an INFO message from my custom logger.")
logger.debug("This DEBUG message will not show because the root level is INFO.")


def validate_environment() -> bool:
    """Validate that all required environment variables are present."""
    logger.info("🔍 Validating environment configuration...")
    
    required_vars = [
        "STRAVA_CLIENT_ID", 
        "STRAVA_CLIENT_SECRET"
    ]
    
    env_file = Path(".env")
    if not env_file.exists():
        logger.warning("No .env file found. Ensure environment variables are set.")
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables in your .env file:")
        for var in missing_vars:
            logger.error(f"  {var}=your_{var.lower()}")
        return False
    
    logger.info("✓ Environment configuration validated")
    return True


def main():
    try:
        log_level = logging.getLogger().getEffectiveLevel()
        logger.info(f"Logging initialized at level: {logging.getLevelName(log_level)}")
        
        if not validate_environment():
            sys.exit(1)
        
        logger.info("🚀 Starting MCP server...")
        logger.info("Your Strava authentication and data handler logs will appear below")
        logger.info("-" * 60)
        
        mcp.run()
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    main()