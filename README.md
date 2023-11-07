# ffmpeg-worker

# Prerequisite:
Docker compose, local testing:
Just do:
  - ``` docker compose up -d ```

And then try testing out by sending message to redis at hostname: localhost


# Environment Variable requirements:

  - AWS_ACCESS_KEY_ID
  - AWS_SECRET_ACCESS_KEY
  - AWS_REGION
  - AWS_BUCKET_NAME
  - REDIS_HOST
  - REDIS_PORT
  - REDIS_FFMPEG_BACKEND_TO_CONVERTER_CHANNEL
  - REDIS_FFMPEG_CONVERTER_TO_THUMBNAIL_CHANNEL
  - REDIS_FFMPEG_THUMBNAIL_TO_CHUNKER_CHANNEL
  - REDIS_FFMPEG_RESPONSE_CHANNEL
  - PATH_TO_PV

GLOBALS (Used in all workers):
  - REDIS_HOST
  - REDIS_PORT
  - REDIS_FFMPEG_RESPONSE_CHANNEL
  - FFMPEG_PATH

Thumbnail:
  - REDIS_FFMPEG_BACKEND_TO_CONVERTER_CHANNEL
  - PATH_TO_PV

Converter:
  - AWS_ACCESS_KEY_ID
  - AWS_SECRET_ACCESS_KEY
  - AWS_REGION
  - AWS_BUCKET_NAME
  - REDIS_FFMPEG_CONVERTER_TO_THUMBNAIL_CHANNEL
  - PATH_TO_PV

Chunker:
  - AWS_ACCESS_KEY_ID
  - AWS_SECRET_ACCESS_KEY
  - AWS_REGION
  - AWS_BUCKET_NAME
  - REDIS_FFMPEG_THUMBNAIL_TO_CHUNKER_CHANNEL

# TODOS:

- Add a monitor to observe the progress of this worker (Probably optional)
