"""RHI API Wrapper - A simple wrapper for rule34 image board."""

from .models import Post, Tag, PostComment, PostDetails, UserProfile
from .client import R34Client, AsyncR34Client, RateLimitError
from .parser import (
    PostParser,
    SidebarParser,
    PostDetailsParser,
    CommentParser,
    UserProfileParser,
)

__all__ = [
    "Post",
    "Tag",
    "PostComment",
    "PostDetails",
    "UserProfile",
    "R34Client",
    "AsyncR34Client",
    "RateLimitError",
    "PostParser",
    "SidebarParser",
    "PostDetailsParser",
    "CommentParser",
    "UserProfileParser",
]
__version__ = "1.0.3"
