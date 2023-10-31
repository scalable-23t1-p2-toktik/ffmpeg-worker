import subprocess

def convert(input_key, output_key, ffmpeg_path):
    # Define the FFmpeg command for the conversion
    ffmpeg_ffmpeg_path = ffmpeg_path + "/ffmpeg"
    ffmpeg_command = f"{ffmpeg_ffmpeg_path} -i {input_key} -c:v libx264 -c:a aac {output_key}"

    # Execute FFmpeg command
    subprocess.call(ffmpeg_command, shell=True)

    # Delete the downloaded video, so that it doesn't consume space
    delete_input_vid = f"rm {input_key}"
    subprocess.call(delete_input_vid, shell=True)

    print('Video conversion complete')

