import youtube_dl
from pathlib import Path
import subprocess
import json

def get_video_list(channel_url, out_file: Path):
    command = [
        "youtube-dl", 
        "--get-filename", 
        "-o", 
        "https://www.youtube.com/watch?v=%(id)s", 
        channel_url
    ]

    # Open a file in write mode
    with out_file.open('w') as file:
        # Execute the command and redirect the output to the file
        subprocess.run(command, stdout=file, text=True)

def get_english_subtitles(video_url):
    print(f'Checking subs for {video_url}')
    ydl_opts = {
        'quiet': True,  # Suppress console output
        'skip_download': True,  # Don't download video
        'writesubtitles': True,  # Attempt to download subtitles
        'writeautomaticsub': False,  # Do not download automatic subtitles
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=False)
        subtitles = info_dict.get('subtitles')
        if subtitles is None:
            print(f"Subtitles are None for {video_url}")
            return []
        valid_subtitles = [sub for sub in subtitles.keys() if 'en' in sub]
        print(valid_subtitles)
        return valid_subtitles
    
def download_video_and_subtitle(video_url, sub_lang='en', output_dir: Path = Path('./downloads'), audio=True, video=True, dummy=True):
    formats = {
        'mp4': video,
        'bestaudio': audio
    }
    format_string = ','.join([key for key, value in formats.items() if value])
    ydl_opts = {
        'writesubtitles': True,   # Write subtitle file
        'writeautomaticsub': False,  # Do not write automatic subtitles
        'subtitleslangs': [sub_lang],  # Desired subtitle language
        'writeinfojson': True,   # Write video metadata to a .info.json file
        'format': format_string,  # Download best video and audio separately
        'verbose': True,  # Print additional info to console
        'postprocessors': [
            {'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'},
            # {'key': 'FFmpegVideoConvertor',
            # 'preferedformat': 'mp4'},  # Convert video to mp4
        ],
        'outtmpl': (output_dir / '%(format_id)s.%(ext)s').absolute().as_posix(),  # Output filename template
    }

    if not dummy:
        for file in output_dir.iterdir():
            file.unlink()
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

    ret_val = {
        "video": None,
        "audio": None,
        "subtitles": None,
        "info": None
    }
    for file in output_dir.iterdir():
        if file.suffix == '.mp4':
            ret_val["video"] = file
        elif file.suffix == '.vtt':
            ret_val["subtitles"] = file
        elif file.suffix == '.mp3':
            ret_val["audio"] = file
        elif file.suffix == '.json':
            ret_val["info"] = json.load(file.open('r'))
    return ret_val

def read_video_list(url_file: Path):
    with open(url_file, 'r') as f:
        video_urls = f.readlines()
    for video_url in video_urls:
        if video_url.lstrip().startswith('#') or video_url.strip() == '':
            continue
        yield video_url.strip()

if __name__ == "__main__":
    video_file_dir = Path('./lists')
    video_file = video_file_dir / './drawfee_videos.txt'
    if not video_file.exists():
        get_video_list('https://www.youtube.com/@Drawfee', video_file)
    with_subs_file = video_file_dir / './drawfee_videos_with_subs.txt'
    without_subs_file = video_file_dir / './drawfee_videos_without_subs.txt'
    if not with_subs_file.exists() or not without_subs_file.exists():
        with with_subs_file.open('w') as f, without_subs_file.open('w') as f2:
            for video_url in read_video_list(video_file):
                print(f'\nChecking {video_url}')
                subs = get_english_subtitles(video_url)
                print(f"Downloading {video_url}" if len(subs) > 0 else f"Skipping {video_url}")
                if len(subs) > 0:
                    f.write(f"{video_url} - {subs[0]}\n")
                    f.flush()
                else:
                    f2.write(f"{video_url}\n")
                    f2.flush()
    else:
        print("Skipping video list generation")

    # for video_url in read_video_list(with_subs_file):
    #     download_video_and_subtitle(video_url, )