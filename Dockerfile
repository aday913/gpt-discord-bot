FROM python:3.11-slim-buster

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . ./

RUN chmod a+x download_audio.sh

CMD ["python", "main.py"]

