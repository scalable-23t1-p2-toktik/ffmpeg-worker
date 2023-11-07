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

def dispatch_message(username, path_to_s3, process_complete, redis_client):
    channel = os.getenv("REDIS_FFMPEG_RESPONSE_CHANNEL")
    if process_complete:
        data = f"200:{username}:{path_to_s3}"
        redis_client.lpush(channel, data)
    else:
        data = f"500:{username}:{path_to_s3}"
        redis_client.lpush(channel, data)


def chunking_video(username, video_name, video_path, bucket_name, redis_client):
    process_complete = False

    try:
        ffmpeg_path = path_correction(os.environ.get("FFMPEG_PATH"))
        pv_path = path_correction(os.environ.get("PATH_TO_PV"))

        path_to_video = pv_path + "/" + video_path
        path_to_chunks = pv_path + "/videos/" + username + "/" + video_name

        hls_command = f"{ffmpeg_path + "/ffmpeg"} -i {path_to_video} -c:v libx264 -g 30 -c:a aac -f segment -segment_time 10 -segment_list {path_to_chunks}/playlist.m3u8 -segment_format mpegts {path_to_chunks}/output%03d.ts"
        try:
            subprocess.call(hls_command, shell=True)
            print("Chunking complete")
        except Exception as e1:
            print(f'An error occurred during chunking: {str(e1)}')
            dispatch_message(username, "None", process_complete, redis_client)

        with open(f"{path_to_chunks}/playlist.m3u8", 'a') as f:
            f.write('\n#EXT-X-IMAGE:thumbnail.jpg\n')


        # List the HLS segment files
        chunked_dir = [os.path.join(path_to_chunks, file) for file in os.listdir(path_to_chunks) if
                         file.startswith('output') and file.endswith('.ts')]

        unique_folder_name = video_name
        output_dir = path_to_chunks
        segment_files = chunked_dir

        try:
            # Upload chunks ts
            for segment_file in segment_files:
                s3.upload_file(segment_file, bucket_name, f'hls/{unique_folder_name}/{segment_file.split("/")[-1]}')

            # Upload the Thumbnail
            s3.upload_file(f'{output_dir}/thumbnail.jpg', bucket_name, f'hls/{unique_folder_name}/thumbnail.jpg')

            # Upload the HLS playlist file
            s3.upload_file(f'{output_dir}/playlist.m3u8', bucket_name, f'hls/{unique_folder_name}/playlist.m3u8')

            print('Upload Complete')

        except Exception as e2:
            print(f"Uploading to S3 failed in chunker worker: {str(e2)}")
            dispatch_message(username, "None", process_complete, redis_client)


        try:
            # Clean up the temporary directory

            subprocess.call(f'rm -r {output_dir}', shell=True)
            subprocess.call(f'rm {path_to_video}', shell=True)

        except Exception as e3:
            print(f"An error occurred during video files cleaning up: {str(e3)}")
            dispatch_message(username, "None", process_complete, redis_client)

        process_complete = True

        # Notify backend that upload succeded
        dispatch_message(username, f'hls/{unique_folder_name}/', process_complete, redis_client)

    except Exception as e:
        print(f'An error occurred in chunker worker: {str(e)}')

        # Notify backend that process failed
        dispatch_message(username, None, redis_client)


def handle_message(message):
    decoded_message = message.decode()
    decoded_message_arr = decoded_message.split(":")
    username = decoded_message_arr[0]
    video_name = decoded_message_arr[1]
    video_path = decoded_message_arr[2]
    bucket_name = os.environ.get("AWS_BUCKET_NAME")
    chunking_video(username, video_name, video_path, bucket_name, redis_client)


def listen_to_redis_channel(redis_client, channel):
    res32 = redis_client.brpop(channel, timeout=0)
    handle_message(res32[1])


if __name__ == '__main__':
    # Change to localhost for local testing
    redis_host = os.environ.get("REDIS_HOST")

    redis_port = os.environ.get("REDIS_PORT")
    channel_name = os.environ.get("REDIS_FFMPEG_CONVERTER_TO_CHUNKER_CHANNEL")

    redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=0)

    print("ffmpeg chunker worker up and running")

    while True:
        listen_to_redis_channel(redis_client, channel_name)

