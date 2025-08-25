from datetime import datetime, timedelta
from stravalib.client import Client
from stravalib.model import DetailedActivity, SummaryActivity
from typing import List, Optional, Tuple
import calendar
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)

class StravaDataHandler:
    def __init__(self, client: Client):
        self.client = client
        self.WORKOUT_TYPE = { "0": "Run_None",
                             "1": "Run_Race",
                             "2": "Run_Long_Run",
                             "3": "Run_Workout",
                             "10": "Ride_None",
                             "11": "Ride_Race",
                             "12": "Ride_Workout"
                            }

    def get_last_week_activities(self, start_ts: int, end_ts: int) -> List[SummaryActivity]:
        """Fetch activities from the last 7 days."""
        start_date = datetime.fromtimestamp(start_ts)
        end_date = datetime.fromtimestamp(end_ts)
        logger.info(f"Fetching activities from {start_date} to {end_date}")

        try:
            activities = list(self.client.get_activities(
                before=end_date,
                after=start_date
            ))
            
            logger.info(f"Retrieved {len(activities)} activities")

            return activities
            
        except Exception as e:
            logger.error(f"Failed to fetch activities: {e}")
            raise

    def get_activity_details(self, activity_id: int) -> DetailedActivity:
        """Get detailed information for a specific activity."""
        try:
            logger.debug(f"Fetching detailed activity id: {activity_id}")
            return self.client.get_activity(activity_id)
        except Exception as e:
            logger.error(f"Failed to fetch activity {activity_id}: {e}")
            raise

    def calculate_pace(self, distance, duration) -> Optional[str]:
        if distance is None or distance == 0:
            return None
        if duration is None or duration == 0:
            return None
        else:
            distance_km = distance/1000
            pace_seconds = duration/distance_km
            minutes, seconds = divmod(pace_seconds, 60)
            # The format specifier :02d pads the integer with a leading zero if necessary
            formatted_time = f"{int(minutes)}:{int(seconds):02d}"
            return formatted_time
    
    def calculate_last_week_timestamps(self) -> Tuple[int, int]:
        """
        Calculate Unix timestamps for the start and end of last week.
        
        Returns:
            Tuple of (after_timestamp, before_timestamp) for last week
        """
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        
        # Start of this week (Monday 00:00:00)
        start_of_this_week = now - timedelta(days=now.weekday())
        start_of_this_week = start_of_this_week.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        
        # Start of last week
        start_of_last_week = start_of_this_week - timedelta(weeks=1)
        
        # End of last week (Sunday 23:59:59)
        end_of_last_week = start_of_this_week - timedelta(seconds=1)
        end_of_last_week = end_of_last_week.replace(
            hour=23, minute=59, second=59, microsecond=0
        )
        
        after_timestamp = calendar.timegm(start_of_last_week.utctimetuple())
        before_timestamp = calendar.timegm(end_of_last_week.utctimetuple())
        
        return after_timestamp, before_timestamp


    def calculate_training_stress_ride(self,
        duration_seconds: Optional[int] = None,
        normalized_power: Optional[float] = None,          # NP (W)
        functional_threshold_power: Optional[float] = None,  # FTP (W)
    ) -> Optional[float]:
        """
        Return Training-Stress Score for a ride

        CYCLING  (Coggan TSS):
            IF  = NP / FTP
            TSS = (duration_seconds * NP * IF) / (FTP * 3600) * 100
        """
        logger.debug("Calculating ride TSS")
        if normalized_power and functional_threshold_power and duration_seconds:
            if functional_threshold_power <= 0:
                return None
            intensity_factor = normalized_power / functional_threshold_power
            tss = (
                duration_seconds
                * normalized_power
                * intensity_factor
                / (functional_threshold_power * 3600)
                * 100
            )
            return round(tss, 2)
        return None
    

    def calculate_training_stress_run(self,
        run_duration_seconds: Optional[int] = None,
        run_distance_m = None,
        threshold_pace_seconds_per_km: Optional[float] = None, # FTPace (s · km-¹)
    ) -> Optional[float]:
        """
        Return Training-Stress Score for a run

        RUNNING (rTSS * pace variant):
            pace_ratio = run_pace / threshold_pace
            rTSS       = (run_duration_seconds * pace_ratio²) / 3600 * 100

        The pace-based rTSS mirrors TrainingPeaks published approach: it treats
        a 1 h run at threshold pace as 100 rTSS and scales stress quadratically with
        intensity.
        """
        logger.debug("Calculating running TSS")
        if run_duration_seconds and run_distance_m and threshold_pace_seconds_per_km:
            run_pace_seconds_per_km: Optional[float] = run_duration_seconds/(run_distance_m/1000)    # average pace  (s · km-¹)
            if threshold_pace_seconds_per_km <= 0 or run_pace_seconds_per_km is None:
                return None
            pace_ratio = run_pace_seconds_per_km / threshold_pace_seconds_per_km
            r_tss = (run_duration_seconds * pace_ratio ** 2) / 3600 * 100
            return round(r_tss, 2)
        return None

    def prepare_training_context(self, activity: DetailedActivity):
        training_stress: Optional[float] = None
        sport_type = activity.sport_type
        run_types = ("Run", "VirtualRun")
        ride_types = ("Ride", "VirtualRide", "EBikeRide")
        if sport_type is not None and sport_type.root in run_types: # type:ignore
            training_stress = self.calculate_training_stress_run(activity.moving_time,
                                                                 activity.distance,
                                                                 255)
        elif sport_type is not None and activity.sport_type in ride_types:
            training_stress = self.calculate_training_stress_ride(activity.moving_time,
                                                                  activity.weighted_average_watts,
                                                                  140)

        return {
            "session_overview": {
                "date": activity.start_date_local.isoformat() if activity.start_date_local is not None else "None",
                "type": sport_type.root if sport_type is not None else activity.type,
                "name": activity.name,
                "description": activity.description,
                "duration_minutes": (activity.moving_time or 0) / 60,
                "distance_km": float(activity.distance) / 1000 if activity.distance else None
            },
            "performance_metrics": {
                "average_pace_min_per_km": self.calculate_pace(activity.distance, activity.moving_time),
                "average_heartrate": activity.average_heartrate,
                "average_cadence": activity.average_cadence,
                "max_heartrate": activity.max_heartrate,
                "elevation_gain_m": float(activity.total_elevation_gain) if activity.total_elevation_gain else None,
                "relative_effort": activity.suffer_score
            },
            "training_load": {
                "calories": activity.calories,
                "average_watts": activity.average_watts,  # cycling
                "training_stress": training_stress,  # custom calculation
            },
            "context": {
                "location": f"{activity.location_city}, {activity.location_state}",
                "conditions": {
                    "indoor": activity.trainer,
                    "commute": activity.commute,
                    "workout": self.WORKOUT_TYPE.get(str(activity.workout_type))
                },
                "subjective_effort": activity.perceived_exertion,
            }
        }
    
    def process_last_week_activities(self) -> List:
        start_date, end_date = self.calculate_last_week_timestamps()
        activity_list = self.get_last_week_activities(start_date, end_date)

        fetch_results: List = []
        for i, activity in enumerate(activity_list):
            if activity.id is not None:
                detailed_activity = self.get_activity_details(activity.id)
                fetch_results.append(self.prepare_training_context(detailed_activity))
        logger.info(f"Fetched {i+1} detailed results")
        return fetch_results
