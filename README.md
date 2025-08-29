# Microblog

Start your own microblog with just one click! (not really one click, but it sounds good)

Here is my version of it: https://microblog.joakimloxdal.se/posts/

I made this as an alternative to twitter.

## How to run the microblog - docker compose

1. Change the default username/password settings in the docker compose file.

2. Run `docker compose up -d` in this directory.

This will start a postgres and a fast api app (using uvicorn) running in a separate container.

You should be able to reach the site using `http:/localhost:8000` (or whichever hostname you want to use).

## How to run the microblog - natively

1. Make sure you have python installed.

2. Install the package with `pip install .`

3. Make sure you have postgres running on your system (I will not tell you how to install postgres, so use docker compose instead if you can't bother)

4. Look at the docker compose file to find which environment variables you need to set for the fastapi app. Set these.

5. Run `alembic upgrade head && uvicorn microblog.app:app --host 0.0.0.0 --port 8000` to have the app running at port 8000 with uvicorn.
