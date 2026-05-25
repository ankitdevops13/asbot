FROM python:3.12.0
RUN apt-get update && apt-get install \
    gcc \
    libffi-dev \
    musl-dev \
    ffmpeg \
    aria2 \
    make \
    g++ \
    cmake && \
    wget -q https://github.com/axiomatic-systems/Bento4/archive/v1.6.0-639.zip && \
    unzip v1.6.0-639.zip && \
    cd Bento4-1.6.0-639 && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make -j$(nproc) && \
    cp mp4decrypt /usr/local/bin/ &&\
    cd ../.. && \
    rm -rf Bento4-1.6.0-639 v1.6.0-639.zip

COPY . /app/
WORKDIR /app/
RUN pip install --upgrade pip -r requirements.txt
CMD gunicorn app:app & python3 bot.py






