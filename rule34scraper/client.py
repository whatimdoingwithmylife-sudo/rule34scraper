"""HTTP client for RHI API."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from .models import Post, Tag, PostDetails, UserProfile
from .parser import PostParser, SidebarParser, PostDetailsParser, UserProfileParser

logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    """Raised when the server returns a 429 Too Many Requests response."""
    pass


def _check_rate_limit(response: httpx.Response) -> httpx.Response:
    """Check response for rate limiting and raise if detected."""
    if response.status_code == 429:
        raise RateLimitError(f"Rate limited: {response.status_code}")
    return response

DEFAULT_BASE_URL = "https://rule34.xxx/index.php"
DEFAULT_POSTS_PER_PAGE = 42

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


class R34Client:
    """Client for interacting with booru-style image boards."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        posts_per_page: int = DEFAULT_POSTS_PER_PAGE,
        headers: Optional[Dict[str, str]] = None,
        max_retries: int = 5,
    ):
        """Initialize the client.

        Args:
            base_url: Base URL for the API (e.g., "https://rule34.xxx/index.php").
            timeout: Request timeout in seconds.
            posts_per_page: Number of posts per page (for pagination offset).
            headers: Custom headers to use (merges with defaults).
            max_retries: Maximum number of retry attempts for rate-limited requests.
        """
        self.base_url = base_url.rstrip("/")
        self.posts_per_page = posts_per_page
        self._timeout = timeout
        self._headers = {**DEFAULT_HEADERS, **(headers or {})}
        self._client: Optional[httpx.Client] = None
        self._max_retries = max_retries

    @property
    def client(self) -> httpx.Client:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.Client(timeout=self._timeout, headers=self._headers)
        return self._client

    def _get(self, url: str, params: Dict = None) -> httpx.Response:
        """Execute GET request with retry logic for rate limits."""
        @retry(
            stop=stop_after_attempt(self._max_retries),
            wait=wait_exponential(multiplier=1, min=1.0, max=60.0),
            retry=retry_if_exception_type((RateLimitError, httpx.TransportError)),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,
        )
        def _request() -> httpx.Response:
            response = self.client.get(url, params=params)
            return _check_rate_limit(response)
        
        return _request()

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self) -> "R34Client":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def get_posts(self, tags: str = "", page: int = 1) -> Tuple[List[Post], List[Tag]]:
        """Fetch posts from the listing page.

        Args:
            tags: Space-separated tag string to filter by.
            page: Page number (1-indexed).

        Returns:
            Tuple of (posts, sidebar_tags).
        """
        offset = (page - 1) * self.posts_per_page
        params = {"page": "post", "s": "list", "tags": tags, "pid": offset}

        response = self._get(self.base_url, params=params)
        response.raise_for_status()

        html = response.text
        posts = PostParser.parse_html(html, self.base_url)
        sidebar_tags = SidebarParser.parse_html(html)

        return posts, sidebar_tags

    def search(self, tags: str, page: int = 1) -> List[Post]:
        """Search for posts by tags."""
        posts, _ = self.get_posts(tags=tags, page=page)
        return posts

    def get_sidebar_tags(self, tags: str = "") -> List[Tag]:
        """Get sidebar tags for a given search."""
        _, sidebar_tags = self.get_posts(tags=tags, page=1)
        return sidebar_tags

    def get_post_details(self, post_id: int) -> Optional[PostDetails]:
        """Fetch detailed info for a specific post."""
        params = {"page": "post", "s": "view", "id": post_id}
        response = self._get(self.base_url, params=params)
        response.raise_for_status()
        return PostDetailsParser.parse_html(response.text)

    def get_user_profile(self, username: str) -> Optional[UserProfile]:
        """Fetch user profile by username."""
        params = {"page": "account", "s": "profile", "uname": username}
        response = self._get(self.base_url, params=params)
        response.raise_for_status()
        return UserProfileParser.parse_html(response.text, self.base_url)

    def download(
        self,
        url: str,
        path: Union[str, Path],
        chunk_size: int = 8192,
    ) -> Path:
        """Download a file from URL."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        download_headers = {
            **self._headers,
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
            "Referer": self.base_url,
        }

        # Bolt: Reuse the client to enable connection pooling and reduce overhead
        with self.client.stream("GET", url, headers=download_headers, follow_redirects=True, timeout=60.0) as response:
            response.raise_for_status()
            with open(path, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=chunk_size):
                    f.write(chunk)

        return path

    def download_post(
        self,
        post: Union[Post, PostDetails, int],
        directory: Union[str, Path] = ".",
        use_sample: bool = False,
    ) -> Path:
        """Download image/video from a post."""
        if isinstance(post, int):
            details = self.get_post_details(post)
            if not details:
                raise ValueError(f"Post {post} not found")
            post = details

        if isinstance(post, PostDetails):
            url = post.sample_url if use_sample else post.image_url
            post_id = post.id
        else:
            details = self.get_post_details(post.id)
            if not details:
                raise ValueError(f"Post {post.id} not found")
            url = details.sample_url if use_sample else details.image_url
            post_id = post.id

        ext = url.split("?")[0].split(".")[-1]
        filename = f"{post_id}.{ext}"
        path = Path(directory) / filename

        return self.download(url, path)


class AsyncR34Client:
    """Async client for interacting with booru-style image boards."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        posts_per_page: int = DEFAULT_POSTS_PER_PAGE,
        headers: Optional[Dict[str, str]] = None,
        max_retries: int = 5,
    ):
        """Initialize the async client.

        Args:
            base_url: Base URL for the API.
            timeout: Request timeout in seconds.
            posts_per_page: Number of posts per page.
            headers: Custom headers to use.
            max_retries: Maximum number of retry attempts for rate-limited requests.
        """
        self.base_url = base_url.rstrip("/")
        self.posts_per_page = posts_per_page
        self._timeout = timeout
        self._headers = {**DEFAULT_HEADERS, **(headers or {})}
        self._client: Optional[httpx.AsyncClient] = None
        self._max_retries = max_retries

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._timeout, headers=self._headers)
        return self._client

    async def _get(self, url: str, params: Dict = None) -> httpx.Response:
        """Execute GET request with retry logic for rate limits."""
        @retry(
            stop=stop_after_attempt(self._max_retries),
            wait=wait_exponential(multiplier=1, min=1.0, max=60.0),
            retry=retry_if_exception_type((RateLimitError, httpx.TransportError)),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,
        )
        async def _request() -> httpx.Response:
            response = await self.client.get(url, params=params)
            return _check_rate_limit(response)
        
        return await _request()

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "AsyncR34Client":
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()

    async def get_posts(self, tags: str = "", page: int = 1) -> Tuple[List[Post], List[Tag]]:
        """Fetch posts from the listing page."""
        offset = (page - 1) * self.posts_per_page
        params = {"page": "post", "s": "list", "tags": tags, "pid": offset}

        response = await self._get(self.base_url, params=params)
        response.raise_for_status()

        html = response.text
        posts = PostParser.parse_html(html, self.base_url)
        sidebar_tags = SidebarParser.parse_html(html)

        return posts, sidebar_tags

    async def search(self, tags: str, page: int = 1) -> List[Post]:
        """Search for posts by tags."""
        posts, _ = await self.get_posts(tags=tags, page=page)
        return posts

    async def get_post_details(self, post_id: int) -> Optional[PostDetails]:
        """Fetch detailed info for a specific post."""
        params = {"page": "post", "s": "view", "id": post_id}
        response = await self._get(self.base_url, params=params)
        response.raise_for_status()
        return PostDetailsParser.parse_html(response.text)

    async def get_user_profile(self, username: str) -> Optional[UserProfile]:
        """Fetch user profile by username."""
        params = {"page": "account", "s": "profile", "uname": username}
        response = await self._get(self.base_url, params=params)
        response.raise_for_status()
        return UserProfileParser.parse_html(response.text, self.base_url)

    async def download(
        self,
        url: str,
        path: Union[str, Path],
        chunk_size: int = 8192,
    ) -> Path:
        """Download a file from URL."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        download_headers = {
            **self._headers,
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
            "Referer": self.base_url,
        }

        # Bolt: Reuse the client to enable connection pooling and reduce overhead
        async with self.client.stream("GET", url, headers=download_headers, follow_redirects=True, timeout=60.0) as response:
            response.raise_for_status()
            with open(path, "wb") as f:
                async for chunk in response.aiter_bytes(chunk_size=chunk_size):
                    f.write(chunk)

        return path

    async def download_post(
        self,
        post: Union[Post, PostDetails, int],
        directory: Union[str, Path] = ".",
        use_sample: bool = False,
    ) -> Path:
        """Download image/video from a post."""
        if isinstance(post, int):
            details = await self.get_post_details(post)
            if not details:
                raise ValueError(f"Post {post} not found")
            post = details

        if isinstance(post, PostDetails):
            url = post.sample_url if use_sample else post.image_url
            post_id = post.id
        else:
            details = await self.get_post_details(post.id)
            if not details:
                raise ValueError(f"Post {post.id} not found")
            url = details.sample_url if use_sample else details.image_url
            post_id = post.id

        ext = url.split("?")[0].split(".")[-1]
        filename = f"{post_id}.{ext}"
        path = Path(directory) / filename

        return await self.download(url, path)
