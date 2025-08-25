from src.strava_mcp.__main__ import main
from src.strava_mcp.auth.strava_auth import StravaAuthenticator
from src.strava_mcp.data.data_handler import StravaDataHandler
from datetime import datetime
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
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
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise
    