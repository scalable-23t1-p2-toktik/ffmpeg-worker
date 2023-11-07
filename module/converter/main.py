import boto3
import subprocess
import redis
import os
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client('s3',
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    region_name=os.environ.get("AWS_REGION"))

def path_correction(path):
    if path[-1] == '/':
        return path.rstrip('/', 1)[0]
    return path


def dispatch_message(username, video_name, path_to_video, process_complete, redis_client):
    if process_complete:
        data = f"{username}:{video_name}:{path_to_video}"
        channel = os.getenv("REDIS_FFMPEG_CONVERTER_TO_THUMBNAIL_CHANNEL")
        redis_client.lpush(channel, data)
    else:
        data = f"500:{username}:None"
        channel = os.getenv("REDIS_FFMPEG_RESPONSE_CHANNEL")
        redis_client.lpush(channel, data)


def process_video(username, video_name, bucket_name, redis_client):
    process_complete = False

    try:
        ffmpeg_path = path_correction(os.environ.get("FFMPEG_PATH"))
        pv_path = path_correction(os.environ.get("PATH_TO_PV"))

        download_to_path = pv_path + "/temp/" + video_name
        if not os.path.exists(pv_path + "/temp"):
            os.mkdir(pv_path + "/temp")
        if not os.path.exists(pv_path + "/chunk-videos"):
            os.mkdir(pv_path + "/chunk-videos")
        if not os.path.exists(pv_path + "/chunk-videos/" + username):
            os.mkdir(pv_path + "/chunk-videos/" + username)
        if not os.path.exists(pv_path + "/converted"):
            os.mkdir(pv_path + "/converted")

        s3.download_file(bucket_name, video_name, download_to_path)

        new_vid_name = video_name.rsplit('.', 1)[0] + ".mp4"

        new_video_path = pv_path + "/converted/" + new_vid_name
        ffmpeg_ffmpeg_path = ffmpeg_path + "/ffmpeg"

        ffmpeg_command = f"{ffmpeg_ffmpeg_path} -i {download_to_path} -c:v libx264 -c:a aac {new_video_path}"

        
        subprocess.call(ffmpeg_command, shell=True)
        
        # Delete the downloaded video, so that it doesn't consume space
        delete_input_vid = f"rm {pv_path + "/temp/" + video_name}"
        subprocess.call(delete_input_vid, shell=True)

        process_complete = True

        print('Converting complete')

        # Notify Redis, convert success
        dispatch_message(username, video_name, "converted/" + new_vid_name, process_complete, redis_client)

    except Exception as e:
        print(f'An error occurred: {str(e)}')

        # Notify backend that process failed
        dispatch_message(username, video_name, "None", process_complete, redis_client)


def handle_message(message):
    decoded_message = message.decode()
    decoded_message_arr = decoded_message.split(":")
    username = decoded_message_arr[0]
    video_name = decoded_message_arr[1]
    bucket_name = os.environ.get("AWS_BUCKET_NAME")
    process_video(username, video_name, bucket_name, redis_client)


def listen_to_redis_channel(redis_client, channel):
    res32 = redis_client.brpop(channel, timeout=0)
    handle_message(res32[1])


if __name__ == '__main__':

    # Change to localhost for local testing
    redis_host = os.environ.get("REDIS_HOST")

    redis_port = os.environ.get("REDIS_PORT")
    channel_name = os.environ.get("REDIS_FFMPEG_BACKEND_TO_CONVERTER_CHANNEL")

    redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=0)

    print("ffmpeg converter worker up and running")

    while True:
        listen_to_redis_channel(redis_client, channel_name)
