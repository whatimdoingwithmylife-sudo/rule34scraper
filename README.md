# rule34scraper

A high-performance Python API wrapper for **Rule34.xxx** (and other booru-style image boards). Built for speed and reliability, it uses `selectolax` (Lexbor engine) for lightning-fast parsing and `httpx` for both synchronous and asynchronous requests.

## Installation

```bash
pip install rule34scraper
```

## Usage

### Basic Searching

Returns a list of `Post` objects from a search result page.

```python
from rule34scraper import R34Client

with R34Client() as client:
    # Search posts by tags (landscape, highres)
    posts, tags = client.get_posts(tags="landscape highres", page=1)
    
    for post in posts:
        print(f"ID: {post.id} | Score: {post.score} | Rating: {post.rating}")
```

### Detailed Metadata (and Creator info)

Search results provide basic info. For full metadata (including the **creator** name, high-res URLs, and comments), use `get_post_details`.

```python
with R34Client() as client:
    posts, _ = client.get_posts(tags="fantasy")
    
    # Get deep details for a specific post
    details = client.get_post_details(posts[0].id)
    
    print(f"Post #{details.id} | Creator: {details.creator.name}")
    print(f"Full Image: {details.image_url} ({details.width}x{details.height})")
    print(f"Tags: {', '.join([t.name for t in details.tags[:5]])}")
```

### Async Usage

Ideal for high-throughput applications.

```python
import asyncio
from rule34scraper import AsyncR34Client

async def main():
    async with AsyncR34Client() as client:
        posts, _ = await client.get_posts(tags="portrait")
        if posts:
            details = await client.get_post_details(posts[0].id)
            print(f"Async Detail Result: {details.id}")

asyncio.run(main())
```

### User Profiles & Favorites

```python
with R34Client() as client:
    profile = client.get_user_profile("username")
    print(f"User: {profile.username} | Level: {profile.level}")
    print(f"Favorites: {profile.favorite_count}")
    
    # Access recent uploads or favorite posts
    for fav in profile.recent_favorites[:5]:
        print(f"Favorite Post: {fav.detail_url}")
```

### Downloading Media

```python
with R34Client() as client:
    details = client.get_post_details(123456)
    # Automatically handles file naming and subdirectory creation
    filepath = client.download_post(details, directory="my_collection")
    print(f"Saved to: {filepath}")
```

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `base_url` | `str` | `https://rule34.xxx` | Base domain for requests. |
| `timeout` | `float` | `30.0` | Request timeout in seconds. |
| `posts_per_page` | `int` | `42` | Default count for pagination. |
| `max_retries` | `int` | `5` | Retry attempts on rate limiting. |
| `headers` | `dict` | *Browser-like* | Custom User-Agent or Cookies. |

## Models

- **Post**: Basic entry from listings (id, preview_url, tags, score, rating).
- **PostDetails**: Full data from the post page (creator, image_url, sample_url, dimensions, comments).
- **Tag**: Tag entry with `name`, `count`, and `type` (e.g., character, artist).
- **UserProfile**: User stats, join date, and lists of recent uploads/favorites.
- **PostComment**: Comment on a post with user, text, and timestamp.

## License

MIT - See the [LICENSE](LICENSE) file for details.
