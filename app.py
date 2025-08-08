"""
one_link_dl.py  –  Paste-a-link Instagram downloader
---------------------------------------------------
• pip install instaloader
• python one_link_dl.py                # will prompt:  Give me the link to download:
• python one_link_dl.py --login USER   # for private posts you can view
"""

import argparse
from urllib.parse import urlparse

from instaloader import Instaloader, Post


def extract_shortcode(url: str) -> str:
    """
    Return the shortcode found inside any Instagram post/Reel/IGTV URL.
    Examples:
      https://www.instagram.com/p/CRrTyF8lNQr/
      https://www.instagram.com/reel/CU7VYT9gX2Q/
      https://www.instagram.com/tv/CF3j-ABm9BH/
    """
    path_parts = [p for p in urlparse(url).path.split("/") if p]   # ['p', 'CRrTyF8lNQr']
    if len(path_parts) >= 2:
        return path_parts[1]
    raise ValueError("Couldn’t locate a shortcode in that URL.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download a single Instagram post, Reel or IGTV video.")
    parser.add_argument("--login", help="Instagram username (required for private links you can view)")
    parser.add_argument("--password", help="Password; omit to be prompted securely")
    args = parser.parse_args()

    # 1. Build Instaloader object
    L = Instaloader(download_video_thumbnails=False, save_metadata=True)

    # 2. Optional login (improves rate-limits & unlocks private content you follow)
    if args.login:
        L.login(args.login, args.password)  # password=None ➟ will ask interactively

    # 3. Ask user for the link interactively
    url = input("Give me the link to download: ").strip()
    try:
        shortcode = extract_shortcode(url)
    except ValueError as err:
        print(f"❌ {err}")
        return

    # 4. Resolve shortcode → Post object, then download
    try:
        post = Post.from_shortcode(L.context, shortcode)
        L.dirname_pattern = "downloads/{profile}"          # ./downloads/<username>/
        L.download_post(post, target=post.owner_username)  # handles photos, videos, Reels
        print("✅ Download complete.")
    except Exception as exc:
        print(f"❌ Download failed: {exc}")


if __name__ == "__main__":
    main()
