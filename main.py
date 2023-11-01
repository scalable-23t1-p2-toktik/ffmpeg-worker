import boto3
import subprocess
import redis
from botocore.config import Config

import os
from dotenv import load_dotenv
from module import converter
from module import chunker

load_dotenv()

s3 = boto3.client('s3', 
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"), 
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"), 
    region_name=os.environ.get("AWS_REGION"))


# # Initialize Redis client
# redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

# Delete this field when redis is implemented
# input_key = "What can I say except.....mp4"

bucket_name = 'toktik-bucket'

def process_video(input_key, bucket_name):
    try:

        ffmpeg_path = os.path.dirname(os.path.abspath(__file__)) + "/ffmpeg"
        
        # Generating output video name in mp4 format
        vid_name_arr = input_key.rsplit('.', 1)
        output_key = "\"" + vid_name_arr[0] + ".mp4" +  "\""

        # Download the input video from S3
        s3.download_file(bucket_name, input_key, "temp/" + input_key)


        input_key = "\"temp/" + input_key + "\""


        converter.convert(input_key, output_key, ffmpeg_path)

        chunk_and_thumbnail_return = chunker.chunk_and_thumbnail(output_key, ffmpeg_path)
        print("Video Chunking Complete")

        unique_folder_name = chunk_and_thumbnail_return[0]
        output_dir = chunk_and_thumbnail_return[1]
        segment_files = chunk_and_thumbnail_return[2]

        # Upload each segment file to S3
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

    except Exception as e:
        print(f'An error occurred: {str(e)}')




def handle_message(message):
    # This function will be called when a message is received on the channel
    process_video(message['data'].decode(), bucket_name)

def listen_to_redis_channel(redis_client, channel):
    pubsub = redis_client.pubsub()
    pubsub.subscribe(channel)

    for message in pubsub.listen():
        if message['type'] == 'message':
            handle_message(message)

if __name__ == '__main__':
    redis_host = 'localhost'  # Replace with your Redis server's host
    redis_port = 6379
    channel_name = 'ffmpeg_channel'  # Replace with your desired channel name

    # Initialize a Redis client
    redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=0)

    print("ffmpeg worker up and running")

    # Start listening to the Redis channel
    listen_to_redis_channel(redis_client, channel_name)
