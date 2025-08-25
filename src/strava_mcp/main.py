import logging
from .auth.strava_auth import StravaAuthenticator
from .data.data_handler import StravaDataHandler
from datetime import datetime
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        # Authenticate with Strava
        auth = StravaAuthenticator()
        client = auth.authenticate()
        handler = StravaDataHandler(client)

        # retrieve and process activity details
        results = handler.process_last_week_activities()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"strava_context_{timestamp}.json"
        data_dir = './.data'
        filepath = f"{data_dir}/{filename}"
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        return filepath
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    main()