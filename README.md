# ffmpeg-worker

# Prerequisite:
First, have a redis server setup and ready:
  - ``` docker run -d -p 6379:6379 redis ```

After that, install the requirements:
  - ``` pip3 install -r requirements.txt ```

# TODOS:

- Add github action and github workflow for this
- Add a monitor to observe the progress of this worker (Probably optional)
- Containerize this worker
- Handle error (Like bad file naming?)
    - Check for all cases of error that could happen too