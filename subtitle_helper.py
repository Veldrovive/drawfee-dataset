import webvtt
from downloader import download_video_and_subtitle
from extract_data import read_video_and_subtitle_lang_list
from pyannote.audio import Pipeline
import os
import torch

from pathlib import Path

def get_subtitles(subtitle_path: Path):
    assert subtitle_path.exists()
    return webvtt.read(subtitle_path.as_posix())

def move_to_accelerator(pipeline: Pipeline):
    if torch.cuda.is_available():
        pipeline.to("cuda")
        print("Using CUDA")
    elif torch.backends.mps.is_available():
        pipeline.to("mps")
        print("Using MPS")
    else:
        pipeline.to("cpu")
        print("Using CPU")

def get_speakers(audio_file: Path, min_speakers=2, max_speakers=5, out_file=None):
    # access_token = os.environ.get("HF_ACCESS_TOKEN")
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization", use_auth_token=True)
    move_to_accelerator(pipeline)
    def hook(step_name, step_artefact, file, *args, **kwargs):
        print(f"{step_name} - {step_artefact} - {file}", args, kwargs, flush=True)
    diarization = pipeline(audio_file.absolute().as_posix(), min_speakers=min_speakers, max_speakers=max_speakers, hook=hook)
    with open(out_file, 'w') as f:
        diarization.write_rttm(f)
    return diarization


if __name__ == "__main__":
    video_file_dir = Path('./lists')
    work_folder = Path('./downloads')
    work_folder.mkdir(exist_ok=True, parents=True)
    video_file = video_file_dir / './drawfee_videos_with_subs.txt'
    for video_url, sub_lang in read_video_and_subtitle_lang_list(video_file):
        print(f"Downloading {video_url} with {sub_lang} subtitles")
        file_data = download_video_and_subtitle(video_url, sub_lang, work_folder, audio=True, video=False, dummy=True)
        info = file_data["info"]
        id = info["id"]
        title = info["title"]
        subtitle_path = file_data["subtitles"]
        audio_path = file_data["audio"]
        print(f"\n\n----------------\nProcessing {title} ({id})")
        print(f"Subtitle path: {subtitle_path}")
        print(f"Audio path: {audio_path}")
        subs = get_subtitles(subtitle_path)
        start_time = subs[0].start
        end_time = subs[-1].end
        print(f"Start time: {start_time} - End time: {end_time}")
        speakers = get_speakers(audio_path, out_file=work_folder / f"{id}.speakers.rttm")
        break
