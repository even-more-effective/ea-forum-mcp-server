#!/usr/bin/env python3
"""
Interactive test client for EA Forum MCP Server
Simulates MCP tool calls without needing a full MCP client
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.server import handle_search_posts, handle_get_post, handle_search_by_tag
from src.config.settings import settings


def print_menu():
    """Print the interactive menu"""
    print("\n" + "="*50)
    print("EA Forum MCP Server - Interactive Test Client")
    print("="*50)
    print("1. Search posts")
    print("2. Get post by ID")
    print("3. Search by tag")
    print("4. Exit")
    print("-"*50)


async def search_posts_interactive():
    """Interactive search posts"""
    print("\n--- Search Posts ---")
    query = input("Enter search query: ").strip()
    if not query:
        print("Search query required!")
        return
    
    # Optional parameters
    print("\nOptional filters (press Enter to skip):")
    date_range = input("Date range (day/week/month/year): ").strip()
    limit_str = input("Number of results (default 10): ").strip()
    curated = input("Curated posts only? (y/n): ").strip().lower() == 'y'
    exclude_events = input("Exclude events? (y/n, default y): ").strip().lower() != 'n'
    
    # Build arguments
    arguments = {"query": query}
    if date_range in ["day", "week", "month", "year"]:
        arguments["date_range"] = date_range
    if limit_str.isdigit():
        arguments["limit"] = int(limit_str)
    arguments["curated_only"] = curated
    arguments["exclude_events"] = exclude_events
    
    print("\nSearching...")
    try:
        results = await handle_search_posts(arguments)
        print("\nResults:")
        print(results[0].text)
    except Exception as e:
        print(f"Error: {str(e)}")


async def get_post_interactive():
    """Interactive get post"""
    print("\n--- Get Post ---")
    post_id = input("Enter post ID: ").strip()
    if not post_id:
        print("Post ID required!")
        return
    
    arguments = {"post_id": post_id}
    
    print("\nFetching post...")
    try:
        results = await handle_get_post(arguments)
        print("\nPost Content:")
        print(results[0].text)
    except Exception as e:
        print(f"Error: {str(e)}")


async def search_by_tag_interactive():
    """Interactive search by tag"""
    print("\n--- Search by Tag ---")
    print("Available tags:")
    for key, info in settings.KNOWN_TAGS.items():
        print(f"  {key}: {info['name']}")
    
    tag = input("\nEnter tag key: ").strip()
    if tag not in settings.KNOWN_TAGS:
        print("Invalid tag!")
        return
    
    limit_str = input("Number of results (default 30): ").strip()
    
    arguments = {"tag": tag}
    if limit_str.isdigit():
        arguments["limit"] = int(limit_str)
    
    print("\nSearching...")
    try:
        results = await handle_search_by_tag(arguments)
        print("\nResults:")
        print(results[0].text)
    except Exception as e:
        print(f"Error: {str(e)}")


async def main():
    """Main interactive loop"""
    print("Welcome to EA Forum MCP Server Interactive Test Client!")
    print("This tool lets you test the MCP server functions directly.")
    
    while True:
        print_menu()
        choice = input("Select option (1-4): ").strip()
        
        if choice == "1":
            await search_posts_interactive()
        elif choice == "2":
            await get_post_interactive()
        elif choice == "3":
            await search_by_tag_interactive()
        elif choice == "4":
            print("\nGoodbye!")
            break
        else:
            print("Invalid choice! Please select 1-4.")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    asyncio.run(main())