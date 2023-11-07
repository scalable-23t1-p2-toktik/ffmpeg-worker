import boto3
import subprocess
import redis
import os
from dotenv import load_dotenv
import random

load_dotenv()



def path_correction(path):
    if path[-1] == '/':
        return path.rstrip('/', 1)[0]
    return path


def dispatch_message(username, video_name, converted_video_path, chunk_video_dir, process_complete, redis_client):
    if process_complete:
        data = f"{username}:{video_name}:{converted_video_path}:{chunk_video_dir}"
        channel = os.getenv("REDIS_FFMPEG_THUMBNAIL_TO_CHUNKER_CHANNEL")
        redis_client.lpush(channel, data)
    else:
        data = f"500:{username}:None"
        channel = os.getenv("REDIS_FFMPEG_RESPONSE_CHANNEL")
        redis_client.lpush(channel, data)


def create_thumbnail(username, video_name, converted_video_path, redis_client):
    process_complete = False
    try:
        ffmpeg_path = path_correction(os.environ.get("FFMPEG_PATH"))
        pv_path = path_correction(os.environ.get("PATH_TO_PV"))

        new_vid_name = video_name.rsplit('.', 1)[0]

        video_path = pv_path + "/" + converted_video_path

        ffprobe_cmd = [
            ffmpeg_path + '/ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ]

        result = subprocess.run(ffprobe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        video_duration = float(result.stdout)
        random_time = random.uniform(0, video_duration)
        thumbnail_path = pv_path + "/chunk-videos/" + username + "/" + new_vid_name
        if not os.path.exists(thumbnail_path):
            os.mkdir(thumbnail_path)
        
        thumbnail_command = f'{ffmpeg_path + "/ffmpeg"} -i {video_path} -ss {random_time} -vframes 1 -q:v 2 {thumbnail_path}/thumbnail.jpg'

        subprocess.call(thumbnail_command, shell=True)

        process_complete = True
        print("Thumbnailing complete")

        # Notify Redis, Thumbnail success
        dispatch_message(username, video_name, video_path, thumbnail_path, process_complete, redis_client)

    except subprocess.CalledProcessError as s:
        print(f'An error occurred in thumbnail worker, during ffmpeg probe: {str(s)}')

    except Exception as e:
        print(f'An error occurred in thumbnail worker: {str(e)}')

        # Notify backend that process failed
        dispatch_message(username, video_name, video_path, "None", process_complete, redis_client)


def handle_message(message):
    decoded_message = message.decode()
    decoded_message_arr = decoded_message.split(":")
    username = decoded_message_arr[0]
    video_name = decoded_message_arr[1]
    converted_video_path = decoded_message_arr[2]
    create_thumbnail(username, video_name, converted_video_path, redis_client)


def listen_to_redis_channel(redis_client, channel):
    res32 = redis_client.brpop(channel, timeout=0)
    handle_message(res32[1])


if __name__ == '__main__':
    # Change to localhost for local testing
    redis_host = os.environ.get("REDIS_HOST")

    redis_port = os.environ.get("REDIS_PORT")
    channel_name = os.environ.get("REDIS_FFMPEG_CONVERTER_TO_THUMBNAIL_CHANNEL")

    redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=0)

    print("ffmpeg thumbnailer worker up and running")

    while True:
        listen_to_redis_channel(redis_client, channel_name)
