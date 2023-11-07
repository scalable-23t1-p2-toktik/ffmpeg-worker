FROM python:3 as thumbnail
COPY requirements.txt /
RUN pip install -r requirements.txt
COPY module/thumbnailer/main.py /
COPY ffmpeg/ /ffmpeg/

# Remove these when ready to push to ghcr
# COPY .env /

CMD [ "python3", "-u", "./main.py" ]

FROM python:3 as converter
COPY requirements.txt /
RUN pip install -r requirements.txt
COPY module/converter/main.py /
COPY ffmpeg/ /ffmpeg/


# Remove these when ready to push to ghcr
# COPY .env /

CMD [ "python3", "-u", "./main.py" ]

FROM python:3 as chunker
COPY requirements.txt /
RUN pip install -r requirements.txt
COPY module/chunker/main.py /
COPY ffmpeg/ /ffmpeg/


# Remove these when ready to push to ghcr
# COPY .env /

CMD [ "python3", "-u", "./main.py" ]