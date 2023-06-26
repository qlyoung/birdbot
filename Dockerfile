FROM python:3.10-bullseye

RUN curl -sSL https://install.python-poetry.org | python3 - --yes
ENV PATH="${PATH}:/root/.local/bin"
WORKDIR /app
COPY yolobirds ./yolobirds
COPY yolov5 ./yolov5
COPY config.yaml pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && poetry install
RUN poetry run pip install -r yolov5/requirements.txt
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6 -y
COPY bot.py .

CMD ["python", "bot.py"]
