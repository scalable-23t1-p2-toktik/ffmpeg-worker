FROM python:3
COPY requirements.txt /
RUN pip install -r requirements.txt
COPY main.py /
COPY ffmpeg/ /ffmpeg/
COPY module/ /module/
COPY output_hls/ /output_hls
COPY temp/ /temp/

# Remove these when ready to push to ghcr
COPY .env /

CMD [ "python3", "./main.py" ]
