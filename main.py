import boto3
import subprocess
import redis
from botocore.config import Config

import os
from dotenv import load_dotenv
from module import converter
from module import chunker
import requests

load_dotenv()

s3 = boto3.client('s3', 
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"), 
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"), 
    region_name=os.environ.get("AWS_REGION"))


bucket_name = 'toktik-bucket'

def dispatch_message(username, key):
    # URL to be decided
    URL = "localhost:"

    if(key != None):
        data = {"status": 200,
                "username": username,
                "s3_directory": key}

        r = requests.post(url=URL, data=data)
    else:
        data = {"status": 500,
                "username": username}
        r = requests.post(url=URL, data=data)

def process_video(username, input_key, bucket_name):
    try:
        ffmpeg_path = os.path.dirname(os.path.abspath(__file__)) + "/ffmpeg"
        
        vid_name_arr = input_key.rsplit('.', 1)
        output_key = "\"" + vid_name_arr[0] + ".mp4" +  "\""

        s3.download_file(bucket_name, input_key, "temp/" + input_key)

        input_key = "\"temp/" + input_key + "\""

        converter.convert(input_key, output_key, ffmpeg_path)

        chunk_and_thumbnail_return = chunker.chunk_and_thumbnail(output_key, ffmpeg_path)
        print("Video Chunking Complete")

        unique_folder_name = chunk_and_thumbnail_return[0]
        output_dir = chunk_and_thumbnail_return[1]
        segment_files = chunk_and_thumbnail_return[2]

        for segment_file in segment_files:
            s3.upload_file(segment_file, bucket_name, f'hls/{unique_folder_name}/{segment_file.split("/")[-1]}')

        # Upload the Thumbnail
        s3.upload_file(f'{output_dir}thumbnail.jpg', bucket_name, f'hls/{unique_folder_name}/thumbnail.jpg')

        # Upload the HLS playlist file
        s3.upload_file(f'{output_dir}playlist.m3u8', bucket_name, f'hls/{unique_folder_name}/playlist.m3u8')

        # Clean up the temporary directory
        subprocess.call(f'rm -r {output_dir}', shell=True)

        print('Upload Complete')

        subprocess.call(f'rm {output_key}', shell=True)

        # Notify backend that upload succeded
        dispatch_message(username, f'hls/{unique_folder_name}/')
        
    except Exception as e:
        print(f'An error occurred: {str(e)}')

        # Notify backend that process failed
        dispatch_message(username, None)



def handle_message(message):
    decoded_message = message.decode()
    decoded_message_arr = decoded_message.split(":")
    username = decoded_message[0]
    video_name = decoded_message[1]
    process_video(username, video_name, bucket_name)

def listen_to_redis_channel(redis_client, channel):
    res32 = redis_client.brpop(channel, timeout=0)
    handle_message(res32[1])

if __name__ == '__main__':
    redis_host = 'localhost'  
    redis_port = 6379
    channel_name = 'ffmpeg_channel'

    redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=0)

    print("ffmpeg worker up and running")
    
    while True:
        listen_to_redis_channel(redis_client, channel_name)

