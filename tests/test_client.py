"""Integration tests against the live Rule34 API."""

import pytest
from rule34scraper.client import AsyncR34Client, R34Client


class TestSyncClient:
    """Tests for the synchronous R34Client."""

    def test_get_posts_returns_results(self):
        """Fetching posts should return a non-empty list."""
        with R34Client() as client:
            posts, tags = client.get_posts(tags="solo", page=1)

            assert len(posts) > 0
            assert len(tags) > 0

    def test_post_has_required_fields(self):
        """Each post should have all required fields populated."""
        with R34Client() as client:
            posts, _ = client.get_posts(tags="solo", page=1)
            post = posts[0]

            assert post.id > 0
            assert post.preview_url.startswith("http")
            assert len(post.tags) > 0
            assert post.rating in ("safe", "questionable", "explicit")
            assert post.detail_url.startswith("http")

    def test_search_returns_posts(self):
        """Search method should return posts matching tags."""
        with R34Client() as client:
            posts = client.search(tags="1girl", page=1)

            assert len(posts) > 0

    def test_get_post_details(self):
        """Fetching post details should return complete info."""
        with R34Client() as client:
            posts, _ = client.get_posts(tags="solo", page=1)
            post_id = posts[0].id

            details = client.get_post_details(post_id)

            assert details is not None
            assert details.id == post_id
            assert details.image_url.startswith("http")
            assert details.width > 0
            assert details.height > 0
            assert details.rating in ("safe", "questionable", "explicit")

    def test_get_sidebar_tags(self):
        """Sidebar tags should have name, count, and type."""
        with R34Client() as client:
            tags = client.get_sidebar_tags(tags="solo")

            assert len(tags) > 0
            tag = tags[0]
            assert tag.name
            assert tag.count >= 0
            assert tag.type

    def test_pagination_returns_different_posts(self):
        """Different pages should return different posts."""
        with R34Client() as client:
            posts_page1, _ = client.get_posts(tags="solo", page=1)
            posts_page2, _ = client.get_posts(tags="solo", page=2)

            ids_page1 = {p.id for p in posts_page1}
            ids_page2 = {p.id for p in posts_page2}

            assert ids_page1 != ids_page2


@pytest.mark.asyncio
class TestAsyncClient:
    """Tests for the asynchronous AsyncR34Client."""

    async def test_get_posts_returns_results(self):
        """Fetching posts should return a non-empty list."""
        async with AsyncR34Client() as client:
            posts, tags = await client.get_posts(tags="solo", page=1)

            assert len(posts) > 0
            assert len(tags) > 0

    async def test_post_has_required_fields(self):
        """Each post should have all required fields populated."""
        async with AsyncR34Client() as client:
            posts, _ = await client.get_posts(tags="solo", page=1)
            post = posts[0]

            assert post.id > 0
            assert post.preview_url.startswith("http")
            assert len(post.tags) > 0
            assert post.rating in ("safe", "questionable", "explicit")
            assert post.detail_url.startswith("http")

    async def test_search_returns_posts(self):
        """Search method should return posts matching tags."""
        async with AsyncR34Client() as client:
            posts = await client.search(tags="1girl", page=1)

            assert len(posts) > 0

    async def test_get_post_details(self):
        """Fetching post details should return complete info."""
        async with AsyncR34Client() as client:
            posts, _ = await client.get_posts(tags="solo", page=1)
            post_id = posts[0].id

            details = await client.get_post_details(post_id)

            assert details is not None
            assert details.id == post_id
            assert details.image_url.startswith("http")
            assert details.width > 0
            assert details.height > 0
            assert details.rating in ("safe", "questionable", "explicit")

    async def test_get_sidebar_tags(self):
        """Sidebar tags should have name, count, and type."""
        async with AsyncR34Client() as client:
            posts, tags = await client.get_posts(tags="solo", page=1)

            assert len(tags) > 0
            tag = tags[0]
            assert tag.name
            assert tag.count >= 0
            assert tag.type

    async def test_pagination_returns_different_posts(self):
        """Different pages should return different posts."""
        async with AsyncR34Client() as client:
            posts_page1, _ = await client.get_posts(tags="solo", page=1)
            posts_page2, _ = await client.get_posts(tags="solo", page=2)

            ids_page1 = {p.id for p in posts_page1}
            ids_page2 = {p.id for p in posts_page2}

            assert ids_page1 != ids_page2
