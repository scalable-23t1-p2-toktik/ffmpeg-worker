import boto3
import subprocess
import redis
import os
from dotenv import load_dotenv
import random

load_dotenv()

s3 = boto3.client('s3',
                  aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                  aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
                  region_name=os.environ.get("AWS_REGION"))


def path_correction(path):
    if path[-1] == '/':
        return path.rstrip('/', 1)[0]
    return path


def dispatch_message(username, video_name, process_complete, redis_client):
    if process_complete:
        data = f"{username}:{video_name}"
        channel = os.getenv("REDIS_FFMPEG_THUMBNAIL_TO_CONVERTER_CHANNEL")
        redis_client.lpush(channel, data)
    else:
        data = f"500:{username}:None"
        channel = os.getenv("REDIS_FFMPEG_RESPONSE_CHANNEL")
        redis_client.lpush(channel, data)


def create_thumbnail(username, video_name, bucket_name, redis_client):
    process_complete = False
    try:
        ffmpeg_path = path_correction(os.environ.get("FFMPEG_PATH"))
        pv_path = path_correction(os.environ.get("PATH_TO_PV"))

        download_to_path = pv_path + "/temp/" + video_name

        s3.download_file(bucket_name, video_name, download_to_path)

        video_location = download_to_path

        ffprobe_cmd = [
            ffmpeg_path + '/ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_location
        ]

        try:
            result = subprocess.run(ffprobe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            video_duration = float(result.stdout)
            random_time = random.uniform(0, video_duration)
            thumbnail_command = f'{ffmpeg_path + "/ffmpeg"} -i {video_location} -ss {random_time} -vframes 1 -q:v 2 {pv_path}/videos/{username}/{video_name}/thumbnail.jpg'

            try:
                subprocess.call(thumbnail_command, shell=True)
            except Exception as e1:
                print(f'An error occurred during thumbnail processing: {str(e1)}')
                dispatch_message(username, video_name, process_complete, redis_client)

        except Exception as e2:
            print(f'An error occurred during ffmpeg probe: {str(e2)}')
            dispatch_message(username, video_name, process_complete, redis_client)

        process_complete = True
        print("Thumbnailing complete")
        # Notify Redis, Thumbnail success
        dispatch_message(username, video_name, process_complete, redis_client)

    except Exception as e:
        print(f'An error occurred in thumbnail worker: {str(e)}')

        # Notify backend that process failed
        dispatch_message(username, video_name, process_complete, redis_client)


def handle_message(message):
    decoded_message = message.decode()
    decoded_message_arr = decoded_message.split(":")
    username = decoded_message_arr[0]
    video_name = decoded_message_arr[1]
    bucket_name = os.environ.get("AWS_BUCKET_NAME")
    create_thumbnail(username, video_name, bucket_name, redis_client)


def listen_to_redis_channel(redis_client, channel):
    res32 = redis_client.brpop(channel, timeout=0)
    handle_message(res32[1])


if __name__ == '__main__':
    # Change to localhost for local testing
    redis_host = os.environ.get("REDIS_HOST")

    redis_port = os.environ.get("REDIS_PORT")
    channel_name = os.environ.get("REDIS_FFMPEG_BACKEND_TO_THUMBNAIL_CHANNEL")

    redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=0)

    print("ffmpeg thumbnailer worker up and running")

    while True:
        listen_to_redis_channel(redis_client, channel_name)
