import streamlit as st
from urllib.parse import urlparse
from instaloader import Instaloader, Post
import os
import shutil
import threading
import time

# Helper to extract shortcode
def extract_shortcode(url: str) -> str:
    path_parts = [p for p in urlparse(url).path.split("/") if p]
    if len(path_parts) >= 2:
        return path_parts[1]
    raise ValueError("❌ Couldn’t locate a shortcode in that URL.")

# Auto delete folder after 2 minutes
def schedule_deletion(path: str, delay: int = 120):
    def delete_folder():
        time.sleep(delay)
        if os.path.exists(path):
            shutil.rmtree(path)
            print(f"🧹 Deleted folder: {path}")
    threading.Thread(target=delete_folder).start()

# Streamlit Page Config
st.set_page_config(page_title="Instagram Downloader", layout="centered")
st.title("📥 Instagram Post/Reel/TV Downloader")

# --- Form UI ---
with st.form("download_form"):
    url = st.text_input("🔗 Enter Instagram Post / Reel / TV URL")
    use_login = st.checkbox("Login to download private posts")

    username = password = None
    if use_login:
        username = st.text_input("👤 Instagram Username", help="Required for private posts")
        password = st.text_input("🔒 Instagram Password", type="password")

    submitted = st.form_submit_button("Download")

# --- On Form Submit ---
if submitted:
    if not url:
        st.error("❗ Please enter a valid Instagram URL.")
    else:
        try:
            shortcode = extract_shortcode(url)
        except ValueError as err:
            st.error(str(err))
        else:
            try:
                st.info("⏳ Downloading from Instagram...")

                # Setup Instaloader
                L = Instaloader(
                    download_video_thumbnails=False,
                    save_metadata=False,
                    download_comments=False,
                    post_metadata_txt_pattern=""
                )

                if use_login and username:
                    L.login(username, password)

                # Get Post Object
                post = Post.from_shortcode(L.context, shortcode)
                username_dir = post.owner_username
                L.dirname_pattern = f"downloads/{username_dir}"
                L.download_post(post, target=username_dir)

                # Scan downloaded folder for media
                download_dir = os.path.join("downloads", username_dir)
                media_files = [
                    f for f in os.listdir(download_dir)
                    if f.endswith(".mp4") or f.endswith(".jpg")
                ]
                media_files.sort()

                if not media_files:
                    st.warning("⚠️ No media found after download.")
                else:
                    st.success(f"✅ {len(media_files)} media file(s) downloaded.")
                    image_files = [f for f in media_files if f.endswith(".jpg")]
                    video_files = [f for f in media_files if f.endswith(".mp4")]

                    if image_files:
                        st.info("📸 Displaying all images from the post:")
                        for i, img_file in enumerate(image_files, start=1):
                            img_path = os.path.join(download_dir, img_file)
                            with open(img_path, "rb") as f:
                                img_bytes = f.read()

                            st.image(img_bytes, use_column_width=True, caption=f"Image {i}")
                            st.download_button(
                                label=f"⬇️ Download Image {i}",
                                data=img_bytes,
                                file_name=img_file,
                                mime="image/jpeg",
                                key=f"img_dl_{i}"
                            )

                    if video_files:
                        st.info("🎥 Displaying video(s):")
                        for i, video in enumerate(video_files, start=1):
                            video_path = os.path.join(download_dir, video)
                            with open(video_path, "rb") as f:
                                video_bytes = f.read()

                            st.video(video_bytes)
                            st.download_button(
                                label=f"⬇️ Download Video {i}",
                                data=video_bytes,
                                file_name=video,
                                mime="video/mp4",
                                key=f"vid_dl_{i}"
                            )

                    # Schedule auto-deletion after 2 mins
                    schedule_deletion(download_dir)

            except Exception as e:
                if "shortcode" in str(e).lower():
                    st.error("❌ Invalid URL or shortcode.")
                elif "Private" in str(e) or "403" in str(e):
                    st.error("🔐 This post is private. Please login to access.")
                else:
                    st.error(f"❌ Error: {e}")
