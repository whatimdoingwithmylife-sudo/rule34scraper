from rule34wrapper import R34Client
import time
import requests

with R34Client() as client:
    # Search posts by tags
    # posts, tags = client.get_posts(tags="video -ai_generated sort:random furry score:>200", page=1)
    # user = client.get_user_profile("babymoon0")
    posts, tags = client.get_posts(tags="video oolay-tiger furry", page=1)
    for post in posts:
        time.sleep(1)

        client.download_post(post, directory="rule34")

  