import subprocess
import redis
import os
from dotenv import load_dotenv

load_dotenv()


def path_correction(path):
    if path[-1] == '/':
        return path.rstrip('/', 1)[0]
    return path


def dispatch_message(username, video_name, path_to_video, process_complete, redis_client):
    if process_complete:
        data = f"{username}:{video_name}:{path_to_video}"
        channel = os.getenv("REDIS_FFMPEG_CONVERTER_TO_CHUNKER_CHANNEL")
        redis_client.lpush(channel, data)
    else:
        data = f"500:{username}:None"
        channel = os.getenv("REDIS_FFMPEG_RESPONSE_CHANNEL")
        redis_client.lpush(channel, data)


def process_video(username, video_name, redis_client):
    process_complete = False

    try:
        ffmpeg_path = path_correction(os.environ.get("FFMPEG_PATH"))
        pv_path = path_correction(os.environ.get("PATH_TO_PV"))

        vid_name_arr = video_name.rsplit('.', 1)
        new_video_name = vid_name_arr[0] + ".mp4"

        new_video_path = pv_path + "/converted/" + new_video_name

        ffmpeg_ffmpeg_path = ffmpeg_path + "/ffmpeg"

        ffmpeg_command = f"{ffmpeg_ffmpeg_path} -i {video_name} -c:v libx264 -c:a aac {new_video_path}"

        try:
            subprocess.call(ffmpeg_command, shell=True)
        except Exception as e1:
            print(f'An error occurred during video conversion: {str(e1)}')
            dispatch_message(username, video_name, "None", process_complete, redis_client)
        finally:
            try:
                # Delete the downloaded video, so that it doesn't consume space
                delete_input_vid = f"rm {pv_path + "/temp/" + video_name}"
                subprocess.call(delete_input_vid, shell=True)
            except Exception as e2:
                print(f'An error occurred during original video deletion: {str(e2)}')
                dispatch_message(username, video_name, "None", process_complete, redis_client)

        process_complete = True

        print('Converting complete')

        # Notify Redis, convert success
        dispatch_message(username, video_name, "converted/" + new_video_name, process_complete, redis_client)

    except Exception as e:
        print(f'An error occurred: {str(e)}')

        # Notify backend that process failed
        dispatch_message(username, video_name, "None", process_complete, redis_client)


def handle_message(message):
    decoded_message = message.decode()
    decoded_message_arr = decoded_message.split(":")
    username = decoded_message_arr[0]
    video_name = decoded_message_arr[1]
    video_duration = decoded_message[2]
    process_video(username, video_name, video_duration, redis_client)


def listen_to_redis_channel(redis_client, channel):
    res32 = redis_client.brpop(channel, timeout=0)
    handle_message(res32[1])


if __name__ == '__main__':

    # Change to localhost for local testing
    redis_host = os.environ.get("REDIS_HOST")

    redis_port = os.environ.get("REDIS_PORT")
    channel_name = os.environ.get("REDIS_FFMPEG_THUMBNAIL_TO_CONVERTER_CHANNEL")

    redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=0)

    print("ffmpeg converter worker up and running")

    while True:
        listen_to_redis_channel(redis_client, channel_name)
