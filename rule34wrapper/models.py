"""Data models for RHI API."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Post:
    """Represents a single thumbnail entry in the grid."""
    id: int
    preview_url: str
    tags: List[str]
    score: int
    rating: str
    detail_url: str
    is_video: bool = False


@dataclass
class Tag:
    """Represents a tag found in the sidebar."""
    name: str
    count: int
    type: str


@dataclass
class PostComment:
    """Represents a user comment on a post."""
    id: int
    username: str
    text: str
    score: int
    timestamp: str


@dataclass
class PostDetails:
    """Represents detailed metadata of a specific post."""
    id: int
    image_url: str
    sample_url: str
    width: int
    height: int
    rating: str
    score: int
    uploader: str
    posted_at: str
    source_url: Optional[str]
    tags: List[Tag]
    comments: List[PostComment]


@dataclass
class UserProfile:
    """Represents a user's profile page."""
    username: str
    id: int
    join_date: str
    level: str
    post_count: int
    deleted_post_count: int
    favorite_count: int
    recent_uploads: List[Post]
    recent_favorites: List[Post]
