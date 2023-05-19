from .downloader import download_video_and_subtitle
from pathlib import Path

def read_video_and_subtitle_lang_list(url_file: Path):
    with open(url_file, 'r') as f:
        video_data = f.readlines()
    for video_string in video_data:
        if video_string.lstrip().startswith('#') or video_string.strip() == '':
            continue
        video_url, sub_lang = video_string.split(" - ")
        yield video_url.strip(), sub_lang.strip()

if __name__ == "__main__":
    video_file_dir = Path('./lists')
    work_folder = Path('./downloads')
    work_folder.mkdir(exist_ok=True, parents=True)
    video_file = video_file_dir / './drawfee_videos_with_subs.txt'
    for video_url, sub_lang in read_video_and_subtitle_lang_list(video_file):
        print(f"Downloading {video_url} with {sub_lang} subtitles")
        download_video_and_subtitle(video_url, sub_lang, work_folder)
        break