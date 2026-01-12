"""Integration tests for parsers against live Rule34 HTML."""

import httpx
import pytest
from rule34scraper.parser import PostParser, PostDetailsParser, SidebarParser

BASE_URL = "https://rule34.xxx/index.php"


def fetch_html(params: dict) -> str:
    """Fetch HTML from Rule34."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
    }
    response = httpx.get(BASE_URL, params=params, headers=headers, timeout=30.0)
    response.raise_for_status()
    return response.text


class TestPostParser:
    """Tests for PostParser against live HTML."""

    def test_parse_post_list(self):
        """Parser should extract posts from listing page."""
        html = fetch_html({"page": "post", "s": "list", "tags": "solo"})
        posts = PostParser.parse_html(html)

        assert len(posts) > 0

    def test_parsed_post_has_valid_id(self):
        """Each parsed post should have a positive ID."""
        html = fetch_html({"page": "post", "s": "list", "tags": "solo"})
        posts = PostParser.parse_html(html)

        for post in posts:
            assert post.id > 0

    def test_parsed_post_has_preview_url(self):
        """Each parsed post should have a preview URL."""
        html = fetch_html({"page": "post", "s": "list", "tags": "solo"})
        posts = PostParser.parse_html(html)

        for post in posts:
            assert post.preview_url.startswith("http")

    def test_parsed_post_has_tags(self):
        """Each parsed post should have at least one tag."""
        html = fetch_html({"page": "post", "s": "list", "tags": "solo"})
        posts = PostParser.parse_html(html)

        for post in posts:
            assert len(post.tags) > 0

    def test_parsed_post_has_rating(self):
        """Each parsed post should have a valid rating."""
        html = fetch_html({"page": "post", "s": "list", "tags": "solo"})
        posts = PostParser.parse_html(html)

        valid_ratings = ("safe", "questionable", "explicit", "unknown")
        for post in posts:
            assert post.rating in valid_ratings


class TestPostDetailsParser:
    """Tests for PostDetailsParser against live HTML."""

    @pytest.fixture
    def post_id(self) -> int:
        """Get a valid post ID from the listing."""
        html = fetch_html({"page": "post", "s": "list", "tags": "solo"})
        posts = PostParser.parse_html(html)
        return posts[0].id

    def test_parse_post_details(self, post_id):
        """Parser should extract details from post page."""
        html = fetch_html({"page": "post", "s": "view", "id": post_id})
        details = PostDetailsParser.parse_html(html)

        assert details is not None
        assert details.id == post_id

    def test_details_has_image_url(self, post_id):
        """Post details should have an image URL."""
        html = fetch_html({"page": "post", "s": "view", "id": post_id})
        details = PostDetailsParser.parse_html(html)

        assert details.image_url.startswith("http")

    def test_details_has_dimensions(self, post_id):
        """Post details should have width and height."""
        html = fetch_html({"page": "post", "s": "view", "id": post_id})
        details = PostDetailsParser.parse_html(html)

        assert details.width > 0
        assert details.height > 0

    def test_details_has_rating(self, post_id):
        """Post details should have a valid rating."""
        html = fetch_html({"page": "post", "s": "view", "id": post_id})
        details = PostDetailsParser.parse_html(html)

        valid_ratings = ("safe", "questionable", "explicit", "unknown")
        assert details.rating in valid_ratings


class TestSidebarParser:
    """Tests for SidebarParser against live HTML."""

    def test_parse_sidebar_tags(self):
        """Parser should extract tags from sidebar."""
        html = fetch_html({"page": "post", "s": "list", "tags": "solo"})
        tags = SidebarParser.parse_html(html)

        assert len(tags) > 0

    def test_sidebar_tag_has_name(self):
        """Each sidebar tag should have a name."""
        html = fetch_html({"page": "post", "s": "list", "tags": "solo"})
        tags = SidebarParser.parse_html(html)

        for tag in tags:
            assert tag.name

    def test_sidebar_tag_has_count(self):
        """Each sidebar tag should have a count >= 0."""
        html = fetch_html({"page": "post", "s": "list", "tags": "solo"})
        tags = SidebarParser.parse_html(html)

        for tag in tags:
            assert tag.count >= 0

    def test_sidebar_tag_has_type(self):
        """Each sidebar tag should have a type."""
        html = fetch_html({"page": "post", "s": "list", "tags": "solo"})
        tags = SidebarParser.parse_html(html)

        for tag in tags:
            assert tag.type
