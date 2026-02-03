from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Tag:
    name: str
    count: int
    type: str


@dataclass
class PostComment:
    id: int
    username: str
    text: str
    score: int
    timestamp: str



@dataclass
class User:
    name: str
    id: Optional[int] = None


@dataclass
class Post:
    id: int
    preview_url: str
    tags: List[str]
    score: int
    rating: str
    detail_url: str
    is_video: bool = False


@dataclass
class PostDetails:
    id: int
    image_url: str
    sample_url: str
    width: int
    height: int
    rating: str
    score: int
    creator: User
    posted_at: str
    source_url: Optional[str]
    tags: List[Tag]
    comments: List[PostComment]


@dataclass
class UserProfile:
    username: str
    id: int
    join_date: str
    level: str
    post_count: int
    deleted_post_count: int
    favorite_count: int
    recent_uploads: List[Post]
    recent_favorites: List[Post]
