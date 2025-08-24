import os
from pathlib import Path
from dotenv import load_dotenv, set_key
from stravalib.client import Client
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class StravaAuthenticator:
    def __init__(self):
        self.client = Client()
        # Strava API Configuration
        self.STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
        self.STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
        self.STRAVA_ACCESS_TOKEN = os.getenv("STRAVA_ACCESS_TOKEN")
        if self.STRAVA_ACCESS_TOKEN is not None:
            self.client.access_token = self.STRAVA_ACCESS_TOKEN
        self.STRAVA_REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")
        self.STRAVA_EXPIRES_AT = os.getenv("STRAVA_EXPIRES_AT")
        if self.STRAVA_EXPIRES_AT is not None:
            self.client.token_expires = int(self.STRAVA_EXPIRES_AT)
        if self.STRAVA_REFRESH_TOKEN is not None:
            self.client.refresh_token = self.STRAVA_REFRESH_TOKEN

    def authenticate(self) -> Client:
        """Authenticate with Strava API using stored tokens."""
        try:
            print(self.STRAVA_ACCESS_TOKEN)
            logger.info(self.client.access_token)
            # Test the connection
            athlete = self.client.get_athlete()
            logger.info(f"Successfully authenticated as {athlete.firstname} {athlete.lastname}")
            
            return self.client
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            self.refresh_token()
            raise

    def refresh_token(self):
        """Refresh the access token using refresh token."""
        try:
            if self.STRAVA_CLIENT_ID is None or self.STRAVA_CLIENT_SECRET is None or self.STRAVA_REFRESH_TOKEN is None:
                raise

            token_response = self.client.refresh_access_token(
                client_id=int(self.STRAVA_CLIENT_ID),
                client_secret=self.STRAVA_CLIENT_SECRET,
                refresh_token=self.STRAVA_REFRESH_TOKEN
            )
            
            # Update tokens (in production, save these securely)
            STRAVA_ACCESS_TOKEN = token_response['access_token']
            STRAVA_REFRESH_TOKEN = token_response['refresh_token']

            # The path to your .env file
            dotenv_path = Path(".env")
            # Ensure the .env file exists
            dotenv_path.touch(mode=0o600, exist_ok=True)

            set_key(dotenv_path, "STRAVA_ACCESS_TOKEN", STRAVA_ACCESS_TOKEN)
            set_key(dotenv_path, "STRAVA_REFRESH_TOKEN", STRAVA_REFRESH_TOKEN)
            
            logger.info("Successfully refreshed access token: ", STRAVA_ACCESS_TOKEN)
            return token_response
            
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise