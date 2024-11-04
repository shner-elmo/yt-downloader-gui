from __future__ import annotations

from io import BytesIO
from contextlib import redirect_stdout

import yt_dlp
import streamlit as st


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

YDL_OPTS = {
    # 'format': 'bestaudio/best' if file_format == "mp3" else 'best',
    # "outtmpl": "%(title)s.%(ext)s",
    "noplaylist": not is_playlist,
    "extract_flat": is_playlist,
    "outtmpl": {"default": "-"},
    "logtostderr": True,
}


def download_video(url: str) -> (BytesIO, str):  # (bytes, title)
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        # Get video info
        info = ydl.extract_info(url, download=False)
        title = info.get("title", "Unknown Title")
        thumbnail_url = info.get("thumbnail")

    st.write(f"**Title:** {title}")
    if thumbnail_url:
        st.image(thumbnail_url, width=300)

    # Set format and quality
    if file_format == "mp3":
        YDL_OPTS["format"] = "bestaudio"
        YDL_OPTS["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": AUDIO_QUALITY[quality],
            }
        ]
    elif file_format == "mp4":
        YDL_OPTS["format"] = "bestvideo+bestaudio"

    # Download the video
    with st.spinner("Downloading video ..."):
        buf = BytesIO()
        with redirect_stdout(buf), yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            ydl.download([url])

    st.success("Download complete")

    return buf, title


def download_bytes(buf: BytesIO, title: str) -> None:
    st.download_button(
        label="Save video",
        data=buf,
        file_name=f"{title} - {quality.lower()}.{file_format}",
        mime="audio/mp3" if file_format == "mp3" else "video/mp4",
    )


def select_playlist_videos_and_download() -> None:  # list of video objects
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        info = ydl.extract_info(url, download=False)

    videos = info.get("entries")
    urls = [x['url'] for x in videos]
    # st.session_state['playlist_videos'] = videos


    def populate_form():
        with st.form("my_form"):
            st.write("### Select videos to download:")

            for i, video in enumerate(videos, start=1):
                st.checkbox(f'{i}\t- {video.get("title")}', key=f"video-checkbox-{i}")

            def on_form_submit():
                checkboxes = (
                    st.session_state[f"video-checkbox-{i}"] for i in range(1, len(videos) + 1)
                )
                selected_urls = [
                    url
                    for url, selected in zip(urls, checkboxes, strict=True)
                    if selected
                ]

                for url in selected_urls:
                    buf, title = download_video(url)
                    download_bytes(buf, title)

            st.form_submit_button("Download", on_click=on_form_submit)

    st.checkbox('Select all', on_change=populate_form)

    populate_form()


if st.button("Download"):
    if url:
        try:
            if not is_playlist:
                buf, title = download_video(url)
                download_bytes(buf, title)
            else:
                select_playlist_videos_and_download()

        except ZeroDivisionError as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Please enter a valid URL.")
