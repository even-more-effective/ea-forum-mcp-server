import logging
from typing import Dict, List, Optional, Any
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

from src.clients.algolia_client import AlgoliaClient
from src.clients.graphql_client import GraphQLClient
from src.config.settings import settings
from src.utils.cache import get_cache
from src.utils.retry import retry_with_backoff

# Configure logging
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

# Initialize server
app = Server(settings.MCP_SERVER_NAME)

# Initialize clients
algolia_client = AlgoliaClient(settings.EA_FORUM_API_BASE_URL, settings.REQUEST_TIMEOUT_SECONDS)
graphql_client = GraphQLClient(settings.EA_FORUM_GRAPHQL_ENDPOINT, settings.REQUEST_TIMEOUT_SECONDS)
cache = get_cache(settings.CACHE_TTL_SECONDS, settings.CACHE_MAX_SIZE)


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available tools"""
    return [
        types.Tool(
            name="search_posts",
            description="Search EA Forum posts using full-text search",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query string",
                    },
                    "date_range": {
                        "type": "string",
                        "description": "Date filter: 'day', 'week', 'month', 'year'",
                        "enum": ["day", "week", "month", "year"],
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of results to return (max 100)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100,
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number (0-based)",
                        "default": 0,
                        "minimum": 0,
                    },
                    "curated_only": {
                        "type": "boolean",
                        "description": "Only return curated posts",
                        "default": False,
                    },
                    "exclude_events": {
                        "type": "boolean",
                        "description": "Exclude event posts",
                        "default": True,
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="get_post",
            description="Get full content of a specific EA Forum post by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "post_id": {
                        "type": "string",
                        "description": "The post ID to retrieve",
                    }
                },
                "required": ["post_id"],
            },
        ),
        types.Tool(
            name="search_by_tag",
            description="Search posts by a specific tag",
            inputSchema={
                "type": "object",
                "properties": {
                    "tag": {
                        "type": "string",
                        "description": "Tag name to search for",
                        "enum": list(settings.KNOWN_TAGS.keys()),
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "default": 30,
                        "minimum": 1,
                        "maximum": 100,
                    },
                },
                "required": ["tag"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls"""
    try:
        if name == "search_posts":
            return await handle_search_posts(arguments)
        elif name == "get_post":
            return await handle_get_post(arguments)
        elif name == "search_by_tag":
            return await handle_search_by_tag(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        logger.error(f"Tool call failed: {str(e)}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


@retry_with_backoff(max_retries=settings.MAX_RETRIES, initial_delay=settings.RETRY_DELAY_SECONDS)
async def handle_search_posts(arguments: dict) -> list[types.TextContent]:
    """Handle search_posts tool call"""
    query = arguments["query"]
    date_range = arguments.get("date_range")
    limit = arguments.get("limit", 10)
    page = arguments.get("page", 0)
    curated_only = arguments.get("curated_only", False)
    exclude_events = arguments.get("exclude_events", True)

    # Check cache
    cache_key = cache.get_search_key(
        query=query,
        date_range=date_range,
        limit=limit,
        page=page,
        curated_only=curated_only,
        exclude_events=exclude_events,
    )
    cached_result = cache.get(cache_key)
    if cached_result:
        return [types.TextContent(type="text", text=cached_result)]

    # Perform search
    results = algolia_client.search_posts(
        search_query=query,
        date_range=date_range,
        limit=limit,
        page=page,
        curated_only=curated_only,
        exclude_events=exclude_events,
    )

    if not results or not results[0]["hits"]:
        response = "No posts found matching your search criteria."
    else:
        posts = results[0]["hits"]
        total_hits = results[0]["nbHits"]
        
        response_parts = [f"Found {total_hits} posts. Showing {len(posts)} results:\n"]
        
        for i, post in enumerate(posts, 1):
            tags = ", ".join(tag["name"] for tag in post.get("tags", []))
            response_parts.append(
                f"\n{i}. **{post['title']}**\n"
                f"   - ID: {post['objectID']}\n"
                f"   - Author: {post['authorDisplayName']}\n"
                f"   - Score: {post['baseScore']}\n"
                f"   - Posted: {post['postedAt']}\n"
                f"   - Tags: {tags}\n"
                f"   - Preview: {post['body'][:200]}...\n"
            )
        
        response = "\n".join(response_parts)

    # Cache the result
    cache.set(cache_key, response)
    
    return [types.TextContent(type="text", text=response)]


@retry_with_backoff(max_retries=settings.MAX_RETRIES, initial_delay=settings.RETRY_DELAY_SECONDS)
async def handle_get_post(arguments: dict) -> list[types.TextContent]:
    """Handle get_post tool call"""
    post_id = arguments["post_id"]

    # Check cache
    cache_key = cache.get_post_key(post_id)
    cached_result = cache.get(cache_key)
    if cached_result:
        return [types.TextContent(type="text", text=cached_result)]

    # Get post content
    post = graphql_client.get_post_by_id(post_id)

    if not post:
        response = f"Post with ID '{post_id}' not found."
    else:
        tags = ", ".join(tag["name"] for tag in post.get("tags", []))
        
        response = (
            f"# {post['title']}\n\n"
            f"**Author:** {post['user']['displayName']} (Karma: {post['user']['karma']})\n"
            f"**Posted:** {post['postedAt']}\n"
            f"**Score:** {post['baseScore']} (Votes: {post['voteCount']})\n"
            f"**Comments:** {post['commentCount']}\n"
            f"**Tags:** {tags}\n"
            f"**Word Count:** {post['contents']['wordCount']}\n\n"
            f"## Content\n\n"
            f"{post['contents']['plaintextDescription']}\n\n"
            f"---\n"
            f"*Full HTML content available in post['contents']['html']*"
        )

    # Cache the result
    cache.set(cache_key, response)
    
    return [types.TextContent(type="text", text=response)]


async def handle_search_by_tag(arguments: dict) -> list[types.TextContent]:
    """Handle search_by_tag tool call"""
    tag_key = arguments["tag"]
    limit = arguments.get("limit", 30)

    if tag_key not in settings.KNOWN_TAGS:
        return [types.TextContent(type="text", text=f"Unknown tag: {tag_key}")]

    tag_info = settings.KNOWN_TAGS[tag_key]
    
    # Search using the tag name
    results = algolia_client.search_by_tag(
        tag_id=tag_info["id"],
        tag_name=tag_info["name"],
        limit=limit,
    )

    if not results or not results[0]["hits"]:
        response = f"No posts found for tag '{tag_info['name']}'."
    else:
        posts = results[0]["hits"]
        
        response_parts = [
            f"Found {len(posts)} posts tagged with '{tag_info['name']}':\n"
        ]
        
        for i, post in enumerate(posts, 1):
            response_parts.append(
                f"\n{i}. **{post['title']}**\n"
                f"   - ID: {post['objectID']}\n"
                f"   - Author: {post['authorDisplayName']}\n"
                f"   - Score: {post['baseScore']}\n"
                f"   - Posted: {post['postedAt']}\n"
            )
        
        response = "\n".join(response_parts)
    
    return [types.TextContent(type="text", text=response)]


async def main():
    """Main entry point"""
    logger.info(f"Starting {settings.MCP_SERVER_NAME} v{settings.MCP_SERVER_VERSION}")
    
    # Run the server
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=settings.MCP_SERVER_NAME,
                server_version=settings.MCP_SERVER_VERSION,
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())