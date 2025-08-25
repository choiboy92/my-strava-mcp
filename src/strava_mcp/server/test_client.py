from fastmcp import Client
import asyncio
from .server import mcp

def test_mcp_server():
    client = Client(mcp)

    async def call_tool(name: str):
        async with client:
            result = await client.call_tool("greet", {"name": name})
            print(result)
    asyncio.run(call_tool("Ford"))
