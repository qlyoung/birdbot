birdbot
=======

Discord bot for querying All About Birds database

Usage
-----

Add the following to `config.yaml`:

```
apikey: <api key>
```

Replacing `<api key>` with your Discord bot API key.

Then `python3 ./bot.py`.

Docker
------
Alternatively, you can run in Docker:

```
docker build --tag birdbot:latest .
docker run birdbot:latest
```
