from datetime import timedelta


def generate_srt_content(segments):
    """
    Generates SRT content from segment list.
    Each segment: {'start': seconds, 'duration': seconds, 'translated': text}
    """
    def format_time(seconds):
        td = timedelta(seconds=seconds)
        total_seconds = td.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        secs = int(total_seconds % 60)
        millis = int((total_seconds - int(total_seconds)) * 1000)
        return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

    srt_content = ""
    for i, seg in enumerate(segments, 1):
        start = seg.get('start', 0)
        duration = seg.get('duration', 0)
        text = seg.get('translated', '') or ''
        text = text.replace("\r", " ").replace("\n", " ")
        start_str = format_time(start)
        end_str = format_time(start + duration)
        srt_content += f"{i}\n{start_str} --> {end_str}\n{text}\n\n"
    return srt_content
