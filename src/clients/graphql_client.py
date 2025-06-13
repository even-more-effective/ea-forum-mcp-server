from typing import Dict, Optional
import requests
from src.models.types import PostContent, GraphQLPostResponse


class GraphQLClient:
    def __init__(self, endpoint: str, timeout: int = 30):
        self.endpoint = endpoint
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def get_post_by_id(self, post_id: str) -> Optional[PostContent]:
        """
        Get full post content using GraphQL

        Args:
            post_id: The post ID from Algolia search

        Returns:
            PostContent dictionary or None if not found
        """
        query = """
        query GetPostById($postId: String!) {
          post(input: {
            selector: {
              _id: $postId
            }
          }) {
            result {
              _id
              title
              slug
              baseScore
              voteCount
              postedAt
              createdAt
              url
              contents {
                html
                plaintextDescription
                wordCount
              }
              user {
                _id
                displayName
                slug
                karma
              }
              tags {
                _id
                name
                slug
              }
              commentCount
              lastCommentedAt
            }
          }
        }
        """

        variables = {"postId": post_id}

        try:
            response = self.session.post(
                self.endpoint,
                json={"query": query, "variables": variables},
                timeout=self.timeout,
            )
            response.raise_for_status()

            data: GraphQLPostResponse = response.json()

            # Extract post from nested response
            if (
                data.get("data")
                and data["data"].get("post")
                and data["data"]["post"].get("result")
            ):
                return data["data"]["post"]["result"]

            return None

        except requests.exceptions.RequestException as e:
            raise Exception(f"GraphQL request failed: {str(e)}")

    def get_posts_by_tag(self, tag_id: str, tag_name: str, limit: int = 30) -> Dict:
        """
        Get posts by specific tag using GraphQL

        Args:
            tag_id: The tag ID to filter by
            tag_name: The tag name
            limit: Number of posts to retrieve

        Returns:
            Dictionary containing posts data
        """
        query = """
        query GetPostsByTag($tagId: String!, $tagName: String!, $limit: Int!) {
          posts(input: {
            terms: {
              filterSettings: {
                tags: [{
                  tagId: $tagId,
                  tagName: $tagName,
                  filterMode: "Required"
                }]
              },
              view: "tagRelevance",
              tagId: $tagId,
              sortedBy: "magic",
              limit: $limit
            }
          }) {
            results {
              _id
              title
              slug
              baseScore
              voteCount
              postedAt
              createdAt
              url
              contents {
                html
                plaintextDescription
                wordCount
              }
              user {
                _id
                displayName
                slug
                karma
              }
              tags {
                _id
                name
                slug
              }
              commentCount
              lastCommentedAt
            }
          }
        }
        """

        variables = {"tagId": tag_id, "tagName": tag_name, "limit": limit}

        try:
            response = self.session.post(
                self.endpoint,
                json={"query": query, "variables": variables},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            raise Exception(f"GraphQL request failed: {str(e)}")

    def close(self):
        """Close the session"""
        self.session.close()