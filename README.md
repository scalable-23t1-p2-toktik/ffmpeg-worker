# ffmpeg-worker

# TODOS:

- Add github action and github workflow for this
- Integrate Redis into this
    - Change input file to come from redis
- Add response to backend, attaching the data uniquely named directory of that video
- Add a monitor to observe the progress of this worker (Probably optional)
- Containerize this worker
- Handle error (Like bad file naming?)
    - Check for all cases of error that could happen too
- Fix the bug where video less than 10 seconds will not be chunked