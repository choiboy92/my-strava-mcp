import logging
from .auth.strava_auth import StravaAuthenticator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        # Authenticate with Strava
        auth = StravaAuthenticator()
        client = auth.authenticate()
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    main()