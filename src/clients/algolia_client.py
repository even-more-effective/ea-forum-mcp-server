import time
from typing import Dict, List, Optional, Union
import requests
from src.models.types import AlgoliaSearchRequest, AlgoliaSearchResult


class AlgoliaClient:
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url
        self.search_endpoint = f"{base_url}/api/search"
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def search_posts(
        self,
        search_query: str,
        date_range: Optional[Union[str, int]] = None,
        limit: int = 10,
        page: int = 0,
        curated_only: bool = False,
        exclude_events: bool = True,
    ) -> List[AlgoliaSearchResult]:
        """
        Search posts using Algolia search API

        Args:
            search_query: The search term
            date_range: 'day', 'week', 'month', 'year', or custom timestamp in ms
            limit: Number of results per page (max ~100)
            page: Page number (0-based)
            curated_only: Filter to only curated posts
            exclude_events: Exclude event posts

        Returns:
            List containing search results
        """
        numeric_filters = []
        facet_filters = []

        # Handle date filtering
        if date_range:
            now_ms = int(time.time() * 1000)
            filter_timestamp = None

            if isinstance(date_range, str):
                time_deltas = {
                    "day": 24 * 60 * 60 * 1000,
                    "week": 7 * 24 * 60 * 60 * 1000,
                    "month": 30 * 24 * 60 * 60 * 1000,
                    "year": 365 * 24 * 60 * 60 * 1000,
                }
                if date_range in time_deltas:
                    filter_timestamp = now_ms - time_deltas[date_range]
            elif isinstance(date_range, (int, float)):
                filter_timestamp = int(date_range)

            if filter_timestamp:
                numeric_filters.append(f"publicDateMs>={filter_timestamp}")

        # Handle facet filters
        if exclude_events:
            facet_filters.append(["isEvent:false"])
        if curated_only:
            facet_filters.append(["curated:true"])

        request_body: AlgoliaSearchRequest = {
            "options": {"emptyStringSearchResults": "empty"},
            "queries": [
                {
                    "indexName": "test_posts",
                    "params": {
                        "hitsPerPage": limit,
                        "query": search_query,
                        "numericFilters": numeric_filters,
                        "tagFilters": "",
                        "page": page,
                    },
                }
            ],
        }

        # Add facet filters if any
        if facet_filters:
            request_body["queries"][0]["params"]["facetFilters"] = facet_filters

        try:
            response = self.session.post(
                self.search_endpoint, json=request_body, timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Search request failed: {str(e)}")

    def search_by_tag(
        self,
        tag_id: str,
        tag_name: str,
        limit: int = 30,
        date_range: Optional[Union[str, int]] = None,
    ) -> List[AlgoliaSearchResult]:
        """
        Search posts by specific tag

        Args:
            tag_id: The tag ID to filter by
            tag_name: The tag name (for search query)
            limit: Number of results
            date_range: Optional date filter

        Returns:
            List containing search results
        """
        # Use tag name as search query and filter by tag
        return self.search_posts(
            search_query=tag_name,
            date_range=date_range,
            limit=limit,
            exclude_events=True,
        )

    def close(self):
        """Close the session"""
        self.session.close()