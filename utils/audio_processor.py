import os
import yt_dlp
from pydub import AudioSegment


DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def download_youtube_audio(url: str) -> str:
    """
    Download YouTube audio and convert it directly to WAV.
    Returns the path of the WAV file.
    """

    output_path = os.path.join(
        DOWNLOAD_DIR,
        "%(title)s.%(ext)s"
    )

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,

        # Use Chrome cookies for YouTube authentication
        "cookiesfrombrowser": ("chrome",),

        # Convert downloaded audio to WAV
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],

        # Don't download playlists
        "noplaylist": True,

        "quiet": False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            # Get the filename yt-dlp used
            filename = ydl.prepare_filename(info)

        # Change extension to WAV
        wav_path = os.path.splitext(filename)[0] + ".wav"

        if not os.path.exists(wav_path):
            raise FileNotFoundError(
                f"WAV file was not created: {wav_path}"
            )

        print(f"Audio downloaded: {wav_path}")

        return wav_path

    except Exception as e:
        print(f"Error downloading YouTube audio: {e}")
        raise


def convert_to_wav(input_path: str) -> str:
    """
    Convert any audio/video file to WAV.
    Output:
        Mono audio
        16 kHz sample rate
    """

    output_path = os.path.splitext(input_path)[0] + "_converted.wav"

    print(f"Converting file: {input_path}")

    audio = AudioSegment.from_file(input_path)

    # Convert to mono + 16 kHz
    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)

    audio.export(
        output_path,
        format="wav"
    )

    print(f"Converted WAV: {output_path}")

    return output_path


def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list:
    """
    Split WAV audio into chunks.

    Example:
        25 minute audio ->
        chunk_0.wav
        chunk_1.wav
        chunk_2.wav
    """

    print("Loading audio for chunking...")

    audio = AudioSegment.from_wav(wav_path)

    chunk_ms = chunk_minutes * 60 * 1000

    chunks = []

    for i, start in enumerate(
        range(0, len(audio), chunk_ms)
    ):
        chunk = audio[start:start + chunk_ms]

        chunk_path = os.path.splitext(wav_path)[0] + f"_chunk_{i}.wav"

        chunk.export(
            chunk_path,
            format="wav"
        )

        chunks.append(chunk_path)

        print(f"Created chunk {i}: {chunk_path}")

    return chunks


def process_input(source: str) -> list:
    """
    Process either:
        1. YouTube URL
        2. Local audio/video file

    Returns:
        List of WAV chunk paths.
    """

    if source.startswith("http://") or source.startswith("https://"):

        print("\nDetected YouTube URL.")
        print("Downloading audio...\n")

        wav_path = download_youtube_audio(source)

    else:

        print("\nDetected local file.")
        print("Converting to WAV...\n")

        wav_path = convert_to_wav(source)

    # Make sure the final audio is suitable for Whisper/RAG
    print("\nConverting audio to 16 kHz mono...")

    audio = AudioSegment.from_wav(wav_path)

    audio = (
        audio
        .set_channels(1)
        .set_frame_rate(16000)
    )

    audio.export(
        wav_path,
        format="wav"
    )

    print("Audio conversion complete.")

    # Split into chunks
    print("\nChunking audio...")

    chunks = chunk_audio(
        wav_path,
        chunk_minutes=10
    )

    print(
        f"\nAudio ready — {len(chunks)} chunk(s) created."
    )

    return chunks


if __name__ == "__main__":

    url = "https://youtu.be/x8C8o1PQmcE?si=07aAfi8t_ZD0gKjs"

    chunks = process_input(url)

    print("\nFinal chunks:")

    for chunk in chunks:
        print(chunk)