#!/usr/bin/env python3
"""
Test script for EA Forum MCP Server
This script tests the server functionality directly without needing an MCP client
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.clients.algolia_client import AlgoliaClient
from src.clients.graphql_client import GraphQLClient
from src.config.settings import settings


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}\n")


async def test_search():
    """Test the Algolia search functionality"""
    print_section("Testing Search Functionality")
    
    client = AlgoliaClient(settings.EA_FORUM_API_BASE_URL, settings.REQUEST_TIMEOUT_SECONDS)
    
    # Test 1: Basic search
    print("1. Basic search for 'AI safety':")
    results = client.search_posts("AI safety", limit=3)
    if results and results[0]["hits"]:
        print(f"   Found {results[0]['nbHits']} total results")
        for i, post in enumerate(results[0]["hits"], 1):
            print(f"   {i}. {post['title']}")
            print(f"      Author: {post['authorDisplayName']}")
            print(f"      Score: {post['baseScore']}")
            print(f"      ID: {post['objectID']}")
    else:
        print("   No results found")
    
    # Test 2: Search with date filter
    print("\n2. Search for 'effective altruism' posts from last week:")
    results = client.search_posts("effective altruism", date_range="week", limit=3)
    if results and results[0]["hits"]:
        print(f"   Found {results[0]['nbHits']} total results from last week")
        for i, post in enumerate(results[0]["hits"], 1):
            posted_date = post['postedAt'][:10]  # Get just the date part
            print(f"   {i}. {post['title']} (posted: {posted_date})")
    else:
        print("   No results found")
    
    # Test 3: Search curated posts only
    print("\n3. Search for curated posts about 'research':")
    results = client.search_posts("research", curated_only=True, limit=3)
    if results and results[0]["hits"]:
        print(f"   Found {results[0]['nbHits']} curated posts")
        for i, post in enumerate(results[0]["hits"], 1):
            print(f"   {i}. {post['title']} (curated: {post.get('curated', False)})")
    else:
        print("   No curated posts found")
    
    client.close()
    return results[0]["hits"][0]["objectID"] if results and results[0]["hits"] else None


async def test_get_post(post_id: str):
    """Test getting full post content"""
    print_section("Testing Get Post Functionality")
    
    client = GraphQLClient(settings.EA_FORUM_GRAPHQL_ENDPOINT, settings.REQUEST_TIMEOUT_SECONDS)
    
    print(f"Getting full content for post ID: {post_id}")
    post = client.get_post_by_id(post_id)
    
    if post:
        print(f"\nTitle: {post['title']}")
        print(f"Author: {post['user']['displayName']} (Karma: {post['user']['karma']})")
        print(f"Score: {post['baseScore']} (Votes: {post['voteCount']})")
        print(f"Comments: {post['commentCount']}")
        print(f"Word Count: {post['contents']['wordCount']}")
        print(f"Tags: {', '.join(tag['name'] for tag in post.get('tags', []))}")
        print(f"\nContent Preview (first 500 chars):")
        print(f"{post['contents']['plaintextDescription'][:500]}...")
    else:
        print("Post not found")
    
    client.close()


async def test_search_by_tag():
    """Test searching by tag"""
    print_section("Testing Search by Tag Functionality")
    
    client = AlgoliaClient(settings.EA_FORUM_API_BASE_URL, settings.REQUEST_TIMEOUT_SECONDS)
    
    # Test with AI Safety tag
    tag_info = settings.KNOWN_TAGS["ai_safety"]
    print(f"Searching for posts with tag: {tag_info['name']}")
    
    results = client.search_by_tag(
        tag_id=tag_info["id"],
        tag_name=tag_info["name"],
        limit=5
    )
    
    if results and results[0]["hits"]:
        print(f"Found {results[0]['nbHits']} posts with '{tag_info['name']}' tag")
        for i, post in enumerate(results[0]["hits"][:5], 1):
            print(f"   {i}. {post['title']}")
            # Show all tags for this post
            tags = [tag['name'] for tag in post.get('tags', [])]
            print(f"      Tags: {', '.join(tags)}")
    else:
        print("No posts found with this tag")
    
    client.close()


async def test_cache():
    """Test caching functionality"""
    print_section("Testing Cache Functionality")
    
    from src.utils.cache import get_cache
    cache = get_cache()
    
    # Test cache operations
    print("1. Testing cache set/get:")
    cache.set("test_key", "test_value")
    value = cache.get("test_key")
    print(f"   Stored: 'test_value', Retrieved: '{value}'")
    print(f"   Cache working: {value == 'test_value'}")
    
    print("\n2. Testing cache miss:")
    missing = cache.get("non_existent_key")
    print(f"   Retrieved: {missing}")
    print(f"   Cache miss working: {missing is None}")
    
    print(f"\n3. Current cache size: {cache.size()}")
    
    cache.clear()
    print(f"4. Cache cleared. New size: {cache.size()}")


async def test_error_handling():
    """Test error handling"""
    print_section("Testing Error Handling")
    
    client = GraphQLClient(settings.EA_FORUM_GRAPHQL_ENDPOINT, settings.REQUEST_TIMEOUT_SECONDS)
    
    print("1. Testing with invalid post ID:")
    try:
        post = client.get_post_by_id("invalid_id_12345")
        if post is None:
            print("   Correctly returned None for invalid ID")
        else:
            print("   Unexpected result:", post)
    except Exception as e:
        print(f"   Error handled: {type(e).__name__}: {str(e)}")
    
    client.close()


async def main():
    """Run all tests"""
    print("EA Forum MCP Server Test Suite")
    print(f"Starting tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Run search test and get a post ID for the next test
        post_id = await test_search()
        
        # Test getting full post content
        if post_id:
            await test_get_post(post_id)
        
        # Test search by tag
        await test_search_by_tag()
        
        # Test cache
        await test_cache()
        
        # Test error handling
        await test_error_handling()
        
        print_section("All Tests Completed Successfully!")
        
    except Exception as e:
        print(f"\nTest failed with error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())