"""Audio rendering -- mux audio layers into video via ffmpeg."""

import subprocess

__all__ = ["mux_audio_into_video", "has_audio_stream"]


def mux_audio_into_video(
    video_path: str,
    output_path: str,
) -> str:
    """Add a silent audio track to a video file via ffmpeg.

    Uses ffmpeg to create a silent stereo audio stream matching video
    duration and mux it into the output.  Full stinger mixing will be
    enhanced in later iterations.

    Returns output_path on success.
    Raises RuntimeError if ffmpeg fails.
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "copy", "-c:a", "aac",
        "-shortest",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg mux failed: {result.stderr}")
    return output_path


def has_audio_stream(video_path: str) -> bool:
    """Check if a video file has an audio stream using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "a",
        "-show_entries", "stream=codec_type",
        "-of", "csv=p=0",
        video_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return "audio" in result.stdout
