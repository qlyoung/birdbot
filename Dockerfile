FROM python:3.10-bullseye

RUN curl -sSL https://install.python-poetry.org | python3 - --yes
ENV PATH="${PATH}:/root/.local/bin"
WORKDIR /app
COPY bot.py config.yaml pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && poetry install

CMD ["python", "bot.py"]
