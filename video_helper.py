import cv2
import matplotlib.pyplot as plt
from tqdm import tqdm
import subprocess
from pathlib import Path
from typing import Optional
import json
import numpy as np
from scipy.ndimage import median_filter

def get_frame_iterator(video_path: Path, compute_every: int = 1):
    assert video_path.exists()
    abs_path = video_path.absolute().as_posix()
    video = cv2.VideoCapture(abs_path)
    current_frame = 0
    while video.isOpened():
        success, frame = video.read()
        if not success:
            break
        if current_frame % compute_every == 0:
            yield current_frame, frame
        current_frame += 1
    video.release()

def get_num_frames(video_path: Path, compute_every: int = 1):
    video = cv2.VideoCapture(video_path.as_posix())
    num_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    video.release()
    return num_frames // compute_every

def extract_frames(video_path: Path, frame_dir: Path, compute_every: Optional[int] = 1):
    """
    ffmpeg -i input.mp4 -vf "select=not(mod(n\,30))" -threads 8 -vsync vfr out_path/%03d.png
    """
    frame_dir.mkdir(exist_ok=True, parents=True)
    args = [
        "ffmpeg",
        "-i",
        video_path.as_posix(),
        "-vf",
        f"select=not(mod(n\\,{compute_every}))",
        "-vsync",
        "vfr",
        (frame_dir / "%03d.png").absolute().as_posix(),
    ]
    print(f"Running {' '.join(args)}")
    subprocess.run(args)

def extract_frames_v2(video_path: Path, output_file: Path, compute_every: Optional[int] = 1):
    """
    ffmpeg -i input.mp4 -vf "select=not(mod(n\,30))" -vsync vfr -c:v libx264 -pix_fmt yuv420p output.mp4
    """
    args = [
        "ffmpeg",
        "-i",
        video_path.absolute().as_posix(),
        "-vf",
        f"select=not(mod(n\\,{compute_every}))",
        "-vsync",
        "vfr",
        "-b:v",
        "100K",
        "-c:v",
        "libx265",
        # "-pix_fmt",
        # "yuv420p",
        output_file.absolute().as_posix(),
    ]
    print(f"Running {' '.join(args)}")
    subprocess.run(args)

def get_frame_iterator_v2(video_path: Path, compute_every: int = 1):
    # temp_frame_dir = Path('./temp_frames')
    # extract_frames(video_path, temp_frame_dir, compute_every)
    # for frame_path in sorted(temp_frame_dir.glob("*.png")):
    #     yield cv2.imread(frame_path.as_posix())
    # temp_frame_dir.rmdir()
    temp_video_path = Path('./temp_video.mp4')
    extract_frames_v2(video_path, temp_video_path, compute_every)
    for i, frame in get_frame_iterator(temp_video_path):
        yield i*compute_every, frame

def plot_channels(frame_nums, channels, postfix: str, y_lab: str, out_file: Path):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(frame_nums, channels[0], label=f"Red {postfix}", color='red')
    ax.plot(frame_nums, channels[1], label=f"Green {postfix}", color='green')
    ax.plot(frame_nums, channels[2], label=f"Blue {postfix}", color='blue')
    ax.set_xlabel('Frame Number')
    ax.set_ylabel(y_lab)
    ax.legend()
    fig.savefig(out_file)

def graph_color_info(video_path: Path, out_dir: Path, compute_every: Optional[int] = None):
    """
    In order to classify drawing changes in the video, we need to calculate some statistics about the colors in a frame
    We will use the mean and standard deviation on each color channel (RGB)
    """
    if compute_every is None:
        video = cv2.VideoCapture(video_path.as_posix())
        fps = int(video.get(cv2.CAP_PROP_FPS))
        compute_every = fps
    if not out_dir.exists():
        out_dir.mkdir(parents=True)

    frame_nums = []
    means = []
    stds = []
    progress_bar = tqdm(total=get_num_frames(video_path, compute_every))
    
    for frame_num, frame in get_frame_iterator_v2(video_path, compute_every):
        mean = frame.mean(axis=(0,1))
        std = frame.std(axis=(0,1))
        means.append(mean)
        stds.append(std)
        frame_nums.append(frame_num)
        progress_bar.update(1)

    means = list(zip(*means))
    stds = list(zip(*stds))

    # Mean plot
    plot_channels(frame_nums, means, "Mean", 'Mean Color Value', out_dir / 'mean_color.png')

    # Standard Deviation plot
    plot_channels(frame_nums, stds, "Std", 'Standard Deviation of Color Value', out_dir / 'std_color.png')


    # Also save the raw data
    with open(out_dir / 'color_info.json', 'w') as f:
        json.dump({
            'means': means,
            'stds': stds,
            'frame_nums': frame_nums
        }, f)

def process_color_info(color_info_path: Path):
    with open(color_info_path) as f:
        color_info = json.load(f)
    means = color_info['means']
    stds = color_info['stds']
    frame_nums = color_info['frame_nums']
    means = np.array(means)
    stds = np.array(stds)

    # Median filter
    means = median_filter(means, size=(1, 500))
    stds = median_filter(stds, size=(1, 500))

    # Normalize
    # means = means / means.max(axis=0)
    # stds = stds / stds.max(axis=0)

    # Calculate the difference between each frame
    # means_diff = np.diff(means, axis=0)
    # stds_diff = np.diff(stds, axis=0)

    plot_channels(frame_nums, means, "Mean Diff", 'Mean Color Value Difference', color_info_path.parent / 'mean_color_diff.png')
    plot_channels(frame_nums, stds, "Std Diff", 'Standard Deviation of Color Value Difference', color_info_path.parent / 'std_color_diff.png')



if __name__ == "__main__":
    video_file = Path('downloads/22.mp4')
    out_dir = Path('downloads/video_info')
    color_info_file = out_dir / 'color_info.json'
    if not color_info_file.exists():
        graph_color_info(video_file, out_dir)
    process_color_info(color_info_file)