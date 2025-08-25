import os
from pathlib import Path
from dotenv import load_dotenv, set_key
from stravalib.client import Client
from stravalib.exc import AccessUnauthorized
import logging
from tenacity import (
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError,
    TryAgain,
    Retrying
)

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
            logger.debug("Access token set on client")
        
        self.STRAVA_EXPIRES_AT = os.getenv("STRAVA_EXPIRES_AT")
        if self.STRAVA_EXPIRES_AT is not None:
            self.client.token_expires = int(self.STRAVA_EXPIRES_AT)
            logger.debug(f"Token expiry set: {self.STRAVA_EXPIRES_AT}")

        self.STRAVA_REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")
        if self.STRAVA_REFRESH_TOKEN is not None:
            self.client.refresh_token = self.STRAVA_REFRESH_TOKEN
            logger.debug("Refresh token configured")

        self.retrier = Retrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type((AccessUnauthorized)),
            reraise=True,
            before_sleep=lambda retry_state: logger.warning(
                f"Retrying authentication (attempt {retry_state.attempt_number}/3)..."
            ),
        )

    def authenticate(self) -> Client:
        """Authenticate with Strava API using stored tokens."""
        while True:
            try:
                for attempt in self.retrier:
                    with attempt:
                        athlete = self.client.get_athlete()
                        logger.info(f"✓ Successfully authenticated as {athlete.firstname} {athlete.lastname}")
                        logger.info(f"✓ Athlete ID: {athlete.id}")
                        return self.client
            except AccessUnauthorized as e:
                self.refresh_token()
                continue
            except RetryError as e:
                logger.error("Failed after multiple retries for transient errors.")
                raise e
            except Exception as e:
                logger.error(f"Authentication failed: {e}")
                raise e


    def refresh_token(self):
        """Refresh the access token using refresh token."""
        try:
            logger.info("Attempting to manually refresh token")
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
            STRAVA_EXPIRES_AT = token_response["expires_at"]

            # The path to your .env file
            dotenv_path = Path(".env")
            # Ensure the .env file exists
            dotenv_path.touch(mode=0o600, exist_ok=True)

            set_key(dotenv_path, "STRAVA_ACCESS_TOKEN", STRAVA_ACCESS_TOKEN)
            set_key(dotenv_path, "STRAVA_REFRESH_TOKEN", STRAVA_REFRESH_TOKEN)
            set_key(dotenv_path, "STRAVA_EXPIRES_AT", str(STRAVA_EXPIRES_AT))
            
            logger.info(f"Successfully refreshed access token: {STRAVA_ACCESS_TOKEN}")
            return token_response
            
        except Exception as e:
            if isinstance(e, AccessUnauthorized):
                raise TryAgain
            else:
                logger.error(f"Token refresh failed: {e}")
                raise