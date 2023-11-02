FROM python:3
COPY requirements.txt /
RUN pip install -r requirements.txt
ENV AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
ENV AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
ENV AWS_REGION=$AWS_REGION
COPY main.py /
COPY ffmpeg/ /ffmpeg/
COPY module/ /module/
COPY output_hls/ /output_hls
COPY temp/ /temp/

# Remove these when ready to push to ghcr
# COPY .env /

CMD [ "python3", "-u", "./main.py" ]
