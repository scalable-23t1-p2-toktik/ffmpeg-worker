FROM python:3
COPY requirements.txt /
RUN pip install -r requirements.txt
COPY module/thumbnailer/main.py /
COPY ffmpeg/ /ffmpeg/

# Remove these when ready to push to ghcr
# COPY .env /

CMD [ "python3", "-u", "./main.py" ]
