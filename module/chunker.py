import subprocess
import uuid
import os
import random

def chunk_and_thumbnail(input_key, ffmpeg_path):
    # Define the directory where the video chunks will be stored temporarily
    output_dir = 'output_hls/'

    # Create a unique folder for this set of chunks
    unique_folder_name = str(uuid.uuid4())
    output_dir += unique_folder_name + '/'

    # Create the temporary directory
    subprocess.call(f'mkdir -p {output_dir}', shell=True)

    input_key = input_key.strip("\"")

    print(input_key)

    ffprobe_cmd = [
        ffmpeg_path + '/ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        input_key
    ]

    result = subprocess.run(ffprobe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    video_duration = float(result.stdout)
    random_time = random.uniform(0, video_duration)

    input_key = "\"" + input_key + "\""

    # Set the desired segment count relative to the video duration
    desired_segment_count = 10  # Adjust as needed

    # Calculate the segment duration based on the video duration
    segment_duration = video_duration / desired_segment_count

    ffmpeg_ffmpeg_path = ffmpeg_path + "/ffmpeg"

    thumbnail_command = f'{ffmpeg_ffmpeg_path} -i {input_key} -ss {random_time} -vframes 1 -q:v 2 {output_dir}thumbnail.jpg'

    subprocess.call(thumbnail_command, shell=True)


    # FFmpeg command to create HLS format chunks with dynamic segment duration
    # hls_command = f"{ffmpeg_ffmpeg_path} -i {input_key} -c:v h264 -hls_time {segment_duration} -hls_list_size 0  -hls_flags split_by_time -hls_segment_filename {output_dir}output%03d.ts {output_dir}playlist.m3u8"
    # subprocess.call(hls_command, shell=True)

    # ffmpeg -i input.mp4 -c:v libx264 -g 30 -c:a aac -f segment -segment_time 10 -segment_list playlist.m3u8 -segment_format mpegts output%03d.ts
    hls_command = f"{ffmpeg_ffmpeg_path} -i {input_key} -c:v libx264 -g 30 -c:a aac -f segment -segment_time 10 -segment_list {output_dir}playlist.m3u8 -segment_format mpegts {output_dir}output%03d.ts"
    subprocess.call(hls_command, shell=True)

    with open(f"{output_dir}playlist.m3u8", 'a') as f:
        f.write('\n#EXT-X-IMAGE:thumbnail.jpg\n')
    
    # List the HLS segment files
    segment_files = [os.path.join(output_dir, file) for file in os.listdir(output_dir) if file.startswith('output') and file.endswith('.ts')]

    return [unique_folder_name, output_dir, segment_files]