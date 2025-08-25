import logging
from .auth.strava_auth import StravaAuthenticator
from .data.data_handler import StravaDataHandler
from .server.server import mcp


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def main():
    try:
        mcp.run()
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    main()