import os
import requests
from dotenv import load_dotenv
from pytubefix import YouTube
import ffmpeg

# Load environment variables from .env file
load_dotenv()

# Get the API key and channel ID from the environment variables
API_KEY = os.getenv("API_KEY")  # Get this Key from the Google Cloud Console by creating a Project and activating YouTube Data API v3
CHANNEL_ID = os.getenv("CHANNEL_ID")  # This ID you can get from your channel by going in your BIO and choosing share channel and Copy Channel ID
DOWNLOAD_PATH = "./downloads"
TRACK_FILE = "downloaded_videos.txt" ##TODO Fix File writinh

# Create downloads directory if it doesn't exist
if not os.path.exists(DOWNLOAD_PATH):
    os.makedirs(DOWNLOAD_PATH)

##TODO Fix Downloaded Tracks logging or maybe switch to DB
def load_downloaded_ids():
    """Load the list of downloaded video IDs from the tracking file."""
    if not os.path.exists(TRACK_FILE):
        return set()

    with open(TRACK_FILE, "r") as file:
        downloaded_ids = set(line.strip() for line in file)
    print(f"Loaded {len(downloaded_ids)} downloaded IDs.")
    return downloaded_ids

def save_downloaded_id(video_id):
    """Save a video ID to the tracking file."""
    with open(TRACK_FILE, "a") as file:
        file.write(f"{video_id}\n")
    print(f"Saved video ID: {video_id}")

def is_video_downloaded(video_id, downloaded_ids):
    """Check if the video has already been downloaded."""
    if video_id in downloaded_ids:
        print(f"Video {video_id} already downloaded.")
        return True
    return False

def download_best_quality(video_url, video_title, video_id, downloaded_ids):
    """Download the highest quality video and audio streams and combine them."""
    try:
        yt = YouTube(video_url)

        # Select the highest resolution video-only stream
        video_stream = yt.streams.filter(adaptive=True, only_video=True, file_extension='mp4').order_by('resolution').desc().first()
        
        # Select the highest quality audio-only stream
        audio_stream = yt.streams.filter(adaptive=True, only_audio=True).order_by('abr').desc().first()

        if video_stream and audio_stream:
            print(f"Downloading video for {video_title} from {video_url}")
            video_file = video_stream.download(output_path=DOWNLOAD_PATH, filename=f"{video_id}_video.mp4")
            print(f"Downloading audio for {video_title} from {video_url}")
            audio_file = audio_stream.download(output_path=DOWNLOAD_PATH, filename=f"{video_id}_audio.mp4")

            # Combine video and audio using ffmpeg-python
            output_file = os.path.join(DOWNLOAD_PATH, f"{video_id}.mp4")
            try:
                (
                    ffmpeg
                    .input(video_file)
                    .input(audio_file)
                    .output(output_file, vcodec='copy', acodec='aac', strict='experimental')
                    .run(overwrite_output=True)
                )
                print(f"Successfully combined: {video_title}")

                # Remove temporary files
                os.remove(video_file)
                os.remove(audio_file)

                save_downloaded_id(video_id)
                downloaded_ids.add(video_id)
                print(f"Downloaded and combined: {video_title}")
            except ffmpeg.Error as e:
                print(f"FFmpeg error: {e.stderr.decode()}")
        else:
            print(f"No suitable streams found for: {video_title}")
    except Exception as e:
        print(f"Error downloading video: {e}")

def get_uploads_playlist_id():
    """Retrieve the uploads playlist ID for the channel."""
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "part": "contentDetails",
        "id": CHANNEL_ID,
        "key": API_KEY
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    items = response.json().get("items", [])
    if not items:
        raise Exception("No channel data found.")
    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

def fetch_videos_from_playlist(playlist_id, downloaded_ids):
    """Fetch videos from the uploads playlist and filter for Shorts."""
    base_url = "https://www.googleapis.com/youtube/v3/playlistItems"
    video_base_url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet,contentDetails",
        "playlistId": playlist_id,
        "maxResults": 100,
        "key": API_KEY
    }

    while True:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        playlist_items = response.json()

        for item in playlist_items.get("items", []):
            video_id = item["contentDetails"]["videoId"]
            video_title = item["snippet"]["title"]
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            # Fetch video details to check the duration
            video_details_params = {
                "part": "contentDetails",
                "id": video_id,
                "key": API_KEY
            }
            video_response = requests.get(video_base_url, params=video_details_params)
            video_response.raise_for_status()
            video_items = video_response.json().get("items", [])

            if video_items:
                duration = video_items[0]["contentDetails"]["duration"]
                # Check if the duration is less than 60 seconds (ISO 8601 duration format)
                if "PT" in duration and ("S" in duration) and "M" not in duration:
                    print(f"Identified Short: {video_title} ({duration})")
                    if not is_video_downloaded(video_id, downloaded_ids):
                        download_best_quality(video_url, video_title, video_id, downloaded_ids)
                else:
                    print(f"Video is not a Short: {video_title} ({duration})")
            else:
                print(f"Could not retrieve video details for: {video_title}")

        next_page_token = playlist_items.get("nextPageToken")
        if not next_page_token:
            break
        params["pageToken"] = next_page_token

def run_daemon():
    """Run the check for new Shorts."""
    downloaded_ids = load_downloaded_ids()
    try:
        uploads_playlist_id = get_uploads_playlist_id()
        print("Checking for new Shorts...")
        fetch_videos_from_playlist(uploads_playlist_id, downloaded_ids)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_daemon()
