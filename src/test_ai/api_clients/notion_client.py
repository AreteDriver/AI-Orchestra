"""Notion API client wrapper."""

from typing import Optional, Dict, List
from test_ai.config import get_settings

try:
    from notion_client import Client as NotionClient
except ImportError:
    NotionClient = None


class NotionClientWrapper:
    """Wrapper for Notion API."""

    def __init__(self):
        settings = get_settings()
        if settings.notion_token and NotionClient:
            self.client = NotionClient(auth=settings.notion_token)
        else:
            self.client = None

    def is_configured(self) -> bool:
        """Check if Notion client is configured."""
        return self.client is not None

    def create_page(self, parent_id: str, title: str, content: str) -> Optional[Dict]:
        """Create a page in Notion."""
        if not self.is_configured():
            return None

        try:
            page = self.client.pages.create(
                parent={"database_id": parent_id},
                properties={"Name": {"title": [{"text": {"content": title}}]}},
                children=[
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {"type": "text", "text": {"content": content}}
                            ]
                        },
                    }
                ],
            )
            return {"id": page["id"], "url": page["url"]}
        except Exception as e:
            return {"error": str(e)}

    def append_to_page(self, page_id: str, content: str) -> Optional[Dict]:
        """Append content to an existing Notion page."""
        if not self.is_configured():
            return None

        try:
            block = self.client.blocks.children.append(
                block_id=page_id,
                children=[
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {"type": "text", "text": {"content": content}}
                            ]
                        },
                    }
                ],
            )
            return {"success": True, "block_id": block["results"][0]["id"]}
        except Exception as e:
            return {"error": str(e)}

    def search_pages(self, query: str) -> List[Dict]:
        """Search for pages in Notion."""
        if not self.is_configured():
            return []

        try:
            results = self.client.search(
                query=query, filter={"property": "object", "value": "page"}
            )
            return [
                {
                    "id": page["id"],
                    "title": page.get("properties", {})
                    .get("Name", {})
                    .get("title", [{}])[0]
                    .get("text", {})
                    .get("content", "Untitled"),
                    "url": page.get("url", ""),
                }
                for page in results.get("results", [])
            ]
        except Exception:
            return []
