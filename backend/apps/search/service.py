"""Meilisearch integration — indexing and search service."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from meilisearch import Client


class SearchService:
    """Meilisearch indexing and search operations."""

    def __init__(self) -> None:
        self.client = Client(
            settings.MEILISEARCH_URL,
            api_key=settings.MEILISEARCH_API_KEY,
        )
        self.prefix = settings.MEILISEARCH_INDEX_PREFIX

    def get_index_name(self, model_name: str) -> str:
        return f"{self.prefix}{model_name}"

    def index_document(self, model_name: str, document: dict[str, Any]) -> None:
        """Index or update a single document."""
        index_name = self.get_index_name(model_name)
        self.client.index(index_name).add_documents([document])

    def delete_document(self, model_name: str, doc_id: str) -> None:
        """Remove a document from search index."""
        index_name = self.get_index_name(model_name)
        self.client.index(index_name).delete_document(doc_id)

    def search(
        self,
        model_name: str,
        query: str,
        filters: str | None = None,
        page: int = 1,
        hits_per_page: int = 25,
    ) -> dict[str, Any]:
        """Execute search against the named index."""
        index_name = self.get_index_name(model_name)
        return self.client.index(index_name).search(
            query,
            {
                "filter": filters,
                "page": page,
                "hitsPerPage": hits_per_page,
            },
        )

    def multi_search(
        self,
        models: list[str],
        query: str,
        filters: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Search across multiple indexes."""
        queries = [
            {
                "indexUid": self.get_index_name(m),
                "q": query,
                "filter": filters,
                "limit": limit,
            }
            for m in models
        ]
        return self.client.multi_search({"queries": queries}) if len(queries) > 1 else {}

    def configure_index(self, model_name: str, settings: dict[str, Any]) -> None:
        """Configure searchable attributes, filters, sort for an index."""
        idx = self.client.index(self.get_index_name(model_name))
        idx.update_settings(settings)

    def health(self) -> bool:
        """Check if Meilisearch is reachable."""
        try:
            self.client.health()
            return True
        except Exception:
            return False
