from fastmcp import FastMCP, Context
from stravalib.model import DetailedActivity
from ..data.data_handler import StravaDataHandler
from ..auth.strava_auth import StravaAuthenticator
import logging

logger = logging.getLogger(__name__)

mcp = FastMCP(
    name="My Strava MCP Server",
    instructions="This server provides operations and data access for my Strava activities"
)

auth = StravaAuthenticator()
client = auth.authenticate()
handler = StravaDataHandler(client)

@mcp.tool
async def greet(name: str, ctx: Context) -> str:
    await ctx.info("greet was called")
    print("Greet is printed")
    logger.info("greet is logged")
    return f"Hello, {name}!"

@mcp.tool
async def get_activity_details_by_id(activity_id: int, ctx: Context) -> DetailedActivity:
    """
    Fetches the full, detailed data for a single activity given its ID.
    Use this to get granular data like power curves or heart rate zones.
    """
    await ctx.info("get_activity_details_by_id was called")
    try:
        # Assuming your data_handler can fetch a single activity by ID
        activity = handler.get_activity_details(activity_id)
        return activity
    except Exception as e:
        raise
