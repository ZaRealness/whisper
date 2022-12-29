import zlib
from typing import Iterator, TextIO


def exact_div(x, y):
    assert x % y == 0
    return x // y


def str2bool(string):
    str2val = {"True": True, "False": False}
    if string in str2val:
        return str2val[string]
    else:
        raise ValueError(f"Expected one of {set(str2val.keys())}, got {string}")


def optional_int(string):
    return None if string == "None" else int(string)


def optional_float(string):
    return None if string == "None" else float(string)


def compression_ratio(text) -> float:
    text_bytes = text.encode("utf-8")
    return len(text_bytes) / len(zlib.compress(text_bytes))


def format_timestamp(seconds: float, always_include_hours: bool = False, decimal_marker: str = '.'):
    assert seconds >= 0, "non-negative timestamp expected"
    milliseconds = round(seconds * 1000.0)

    hours = milliseconds // 3_600_000
    milliseconds -= hours * 3_600_000

    minutes = milliseconds // 60_000
    milliseconds -= minutes * 60_000

    seconds = milliseconds // 1_000
    milliseconds -= seconds * 1_000

    hours_marker = f"{hours:02d}:" if always_include_hours or hours > 0 else ""
    return f"{hours_marker}{minutes:02d}:{seconds:02d}{decimal_marker}{milliseconds:03d}"


def write_txt(transcript: Iterator[dict], file: TextIO):
    for segment in transcript:
        print(segment['text'].strip(), file=file, flush=True)


def write_vtt(transcript: Iterator[dict], file: TextIO):
    print("WEBVTT\n", file=file)
    for segment in transcript:
        print(
            f"{format_timestamp(segment['start'])} --> {format_timestamp(segment['end'])}\n"
            f"{segment['text'].strip().replace('-->', '->')}\n",
            file=file,
            flush=True,
        )


def write_srt(transcript: Iterator[dict], file: TextIO, max_line_length: int = 42):
    """
    Write a transcript to a file in SRT format.

    Example usage:
        from pathlib import Path
        from whisper.utils import write_srt

        result = transcribe(model, audio_path, temperature=temperature, **args)

        # save SRT
        audio_basename = Path(audio_path).stem
        with open(Path(output_dir) / (audio_basename + ".srt"), "w", encoding="utf-8") as srt:
            write_srt(result["segments"], file=srt)
    """
    
    comma_split_threshold = int(float(max_line_length) * 0.75)
    
    for i, segment in enumerate(transcript, start=1):
        
        # left the .replace() here to not change unnecessarily
        # but I don't think it's needed?
        segment_text = segment['text'].strip().replace('-->', '->')
        
        if len(segment_text) > max_line_length:
            segment_text = split_text_into_multiline(segment_text, max_line_length, comma_split_threshold)
        
        # write srt lines
        print(
            f"{i}\n"
            f"{format_timestamp(segment['start'], always_include_hours=True, decimal_marker=',')} --> "
            f"{format_timestamp(segment['end'], always_include_hours=True, decimal_marker=',')}\n"
            f"{segment_text}\n",
            file=file,
            flush=True,
        )


def split_text_into_multiline(segment_text: str, max_line_length: int, comma_split_threshold: int):
    
    words = segment_text.split(' ')
    
    lines = [
        words[0]
    ]
    
    for word in words[1:]:
        current_line = lines[-1]
        
        # start a new line if the last word ended with a comma,
        # and we're mostly through this line
        if current_line.endswith(',') and len(current_line) > comma_split_threshold:
            lines.append(word)
            continue
        
        line_with_word = f'{current_line} {word}'
        
        if len(line_with_word) > max_line_length:
            lines.append(word)
        else:
            lines[-1] = line_with_word
    
    return '\n'.join(lines)

