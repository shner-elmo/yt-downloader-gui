from __future__ import annotations

import streamlit as st
import yt_dlp
from io import BytesIO
from contextlib import redirect_stdout

AUDIO_QUALITY = {
    "High": 192,
    "Medium": 128,
    "Low": 64,
}

st.title("YouTube Downloader")
url = st.text_input("Enter YouTube Video URL")
is_playlist = st.checkbox("Is this a playlist?")
file_format = st.selectbox("Select Format", ["mp3", "mp4"])
quality = st.selectbox("Audio Quality", tuple(AUDIO_QUALITY.keys()))

ydl_opts = {
    # 'format': 'bestaudio/best' if file_format == "mp3" else 'best',
    # "outtmpl": "%(title)s.%(ext)s",
    "noplaylist": not is_playlist,
    "extract_flat": is_playlist,
    "outtmpl": {"default": "-"},
    "logtostderr": True,
}


def download_video(url: str) -> (BytesIO, str):  # (bytes, title)
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Get video info
        info = ydl.extract_info(url, download=False)
        title = info.get("title", "Unknown Title")
        thumbnail_url = info.get("thumbnail")
    st.write(f"**Title:** {title}")
    if thumbnail_url:
        st.image(thumbnail_url, width=300)

    # Set format and quality
    if file_format == "mp3":
        ydl_opts["format"] = "bestaudio"
        ydl_opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": AUDIO_QUALITY[quality],
            }
        ]
    elif file_format == "mp4":
        ydl_opts["format"] = "bestvideo+bestaudio"

    # Download the video
    with st.spinner("Downloading video ..."):
        buf = BytesIO()
        with redirect_stdout(buf), yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    st.success('Download complete')

    return buf, title


def download_bytes(buf: BytesIO, title: str) -> None:
    st.download_button(
        label="Download File",
        data=buf,
        file_name=f"{title}.{file_format}",
        mime="audio/mp3" if file_format == "mp3" else "video/mp4",
    )


if st.button("Download"):
    if url:
        try:
            if not is_playlist:
                buf, title = download_video(url)
                download_bytes(buf, title)
            else:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)

                with st.form("my_form"):
                    st.write("### Select videos to download:")

                    entries = info.get("entries") if is_playlist else [info]
                    videos = []
                    print("videos = [")
                    for i, video in enumerate(entries, start=1):
                        title = video.get("title", f"Video {i}")
                        # add number to the key so its "guaranteed" to be unique
                        checkbox_key = f"{title} ({i})"
                        ck = st.checkbox(f"{title}", key=f"{title} ({i})")
                        videos.append((ck, video))
                        print("added vid")

                    if st.form_submit_button(
                        "Download",
                        on_click=lambda: (
                            print(videos),
                            [download_video(vid, info) for x, vid in videos if x],
                        ),
                    ):
                        print("yeah?")
                        for x in videos:
                            print(x)

        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Please enter a valid URL.")
