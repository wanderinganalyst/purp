# Running the Flask app with Docker

This page describes how to build and run the `purp` Flask app in Docker on macOS (zsh). Use these instructions when you want a containerized, production-like run (the image uses `gunicorn`).

Prerequisites
- Docker installed and running: https://docs.docker.com/get-docker/
- (Optional) docker-compose if you prefer compose commands: https://docs.docker.com/compose/install/

Project layout (relevant files)
- `main.py` — Flask app entrypoint.
- `requirements.txt` — Python dependencies (`Flask`, `gunicorn`).
- `Dockerfile` — build instructions for the image.
- `docker-compose.yml` — convenience for local runs.

Build the image (recommended)

```bash
# from repository root
docker build -t flask-hello .
```

Run the container

```bash
# run the container and map container port 5000 -> host 5000
docker run --rm -p 5000:5000 flask-hello
```

Then open http://127.0.0.1:5000 in your browser.

Using docker-compose

```bash
# from repository root
docker-compose up --build
```

This will build the image (if needed) and run the `web` service exposing port `5000`.

Development tips
- If you want live-reload during development, run the app via the Flask CLI (not gunicorn) and mount the source into the container. Example `docker-compose.override.yml` could mount `.` into `/app` and set the command to `flask run --host=0.0.0.0 --reload`.
- Example quick dev run (no Dockerfile change):

```bash
docker run --rm -it -p 5000:5000 -v "$(pwd)":/app -w /app python:3.11-slim \
  bash -lc "pip install --no-cache-dir -r requirements.txt && FLASK_APP=main.py flask run --host=0.0.0.0 --reload"
```

Initializing the database (Postgres) and seeding demo users
-------------------------------------------------------

After the Postgres service is running, initialize the database schema and create the demo users (only needs to be done once):

```bash
# start the database only (if you haven't already started both services)
docker-compose up -d db

# run the init_db script inside a one-off web container; this will use the same DATABASE_URL from docker-compose
docker-compose run --rm web python init_db.py
```

The `init_db.py` script uses SQLAlchemy to create tables and insert two demo users if they don't already exist:

- regular / password  (role: regular)
- power / powerpass   (role: power)

If you prefer the init step to run inside the running web container (instead of a one-off), you can exec into the web container when it's up and run the command there.

Host Postgres port note
------------------------

By default the compose file maps the Postgres container port 5432 to host port 5433 to avoid conflicts with a local Postgres instance that often listens on 5432. If you need to use a different host port, set the `HOST_DB_PORT` environment variable when starting compose. Example:

```bash
# start compose with web on host port 5001 and Postgres on host port 5432
HOST_PORT=5001 HOST_DB_PORT=5432 docker-compose up --build
```

Inside the containers the database still listens on port 5432, so the `DATABASE_URL` in `docker-compose.yml` remains `postgresql://postgres:example@db:5432/flaskdb` and does not need to change.

Troubleshooting
---------------
- If `docker-compose run web python init_db.py` fails because Postgres isn't ready yet, wait a few seconds and run it again. You can also check Postgres logs with `docker-compose logs db`.
- If you changed `DATABASE_URL` or Postgres credentials in `docker-compose.yml`, use the matching values when starting the DB and running the init script.

Port conflict / host port already in use
--------------------------------------

If your host machine already has a process listening on port 5000 (the default mapping), Docker will fail with an error like:

```
Error response from daemon: ports are not available: exposing port TCP 0.0.0.0:5000 -> 127.0.0.1:0: listen tcp 0.0.0.0:5000: bind: address already in use
```

Options to resolve this:

- Stop the process using port 5000 (macOS / Linux):

```bash
# show the process using port 5000
lsof -i :5000
# note the PID column and stop it (replace <PID> with the number)
kill <PID>
```

- Change the host port Docker binds to by setting the HOST_PORT environment variable when starting compose. The `docker-compose.yml` is configured to use `${HOST_PORT:-5000}:5000`, so you can pick a free host port (for example 5001):

```bash
HOST_PORT=5001 docker-compose up --build
```

- Alternatively, edit `docker-compose.yml` and change the `ports` mapping under the `web` service from `- "5000:5000"` to another host port like `- "5001:5000"`.

If you'd like I can add a small helper script that detects an in-use port and prompts you to pick a different host port before starting compose.

Environment variables
- `FLASK_APP` is set in the Dockerfile to `main.py`. For other configs you can pass environment variables with `-e NAME=value` to `docker run` or add them to `docker-compose.yml`.

Rebuilding after code or dependency changes
- If you change `requirements.txt`, rebuild the image to install new dependencies:

```bash
docker build --no-cache -t flask-hello .
```

- If only code changes and you mount the source (dev mode), you may not need to rebuild the image.

Healthchecks and production
- For production use, consider adding a Docker `HEALTHCHECK` instruction or configuring an external healthcheck (k8s, ECS). You may also want to add a dedicated production config, logging, and a non-root user in the Dockerfile.

Troubleshooting
- Image fails to build: check the `pip` output in the build logs; ensure your base image and Python version are compatible.
- Port already in use: ensure nothing else is listening on host port 5000 or map to another host port (e.g. `-p 8080:5000`).
- Gunicorn errors: review container logs (`docker logs <container>`) and ensure `main:app` points to your Flask app object.

Commands reference

- Build: `docker build -t flask-hello .`
- Run: `docker run --rm -p 5000:5000 flask-hello`
- Compose: `docker-compose up --build`
- Stop compose: `docker-compose down`

If you'd like, I can add a `docker-compose.override.yml` for development (with volume mounts and reload) or a `Dockerfile.dev` optimized for rapid iteration.

Automated requirements/security checks
-------------------------------------

This repo includes a lightweight security/outdated dependency checker at `scripts/check_requirements.py`. It:

- Reads `requirements.txt`.
- Checks PyPI for the latest released version of each listed package.
- Queries the OSV (Open Source Vulnerabilities) API for known vulnerabilities for the package/version.
- Writes a JSON and a human-readable text report under `reports/`.

You can run it locally (needs `requests` and `packaging`):

```bash
pip install requests packaging
python scripts/check_requirements.py requirements.txt
# reports/requirements_report.json
# reports/requirements_report.txt
```

There's also a GitHub Actions workflow `.github/workflows/requirements-check.yml` that runs the checker on pushes/PRs and uploads the reports as workflow artifacts.

Quick launcher script
---------------------

To make starting the stack easier when host ports are already in use, a small helper script is provided at `scripts/docker-start.sh`.

Usage:

```bash
# make executable (first time)
chmod +x scripts/docker-start.sh

# interactive: will suggest free ports and ask for confirmation
./scripts/docker-start.sh

# non-interactive: auto-pick free ports and start
./scripts/docker-start.sh -y

# or explicitly set environment ports
HOST_PORT=5001 HOST_DB_PORT=5432 ./scripts/docker-start.sh -y
```

The script tries `docker-compose` first, then falls back to `docker compose` if available. It will export `HOST_PORT` and `HOST_DB_PORT` before invoking compose, so you don't need to edit `docker-compose.yml`.

CI / CD to Azure via GitHub Actions
----------------------------------

This repository includes a sample GitHub Actions workflow at `.github/workflows/azure-deploy.yml` that builds the Docker image, pushes it to Azure Container Registry (ACR), and updates an Azure Web App for Containers to use the new image.

Required GitHub repository secrets
 - `AZURE_CREDENTIALS` — JSON credentials for a service principal. Create with:

```bash
az ad sp create-for-rbac --name "github-deploy-sp" \
  --role contributor \
  --scopes /subscriptions/<SUBSCRIPTION_ID>/resourceGroups/<RESOURCE_GROUP> \
  --sdk-auth
```

Copy the JSON output and add it as the `AZURE_CREDENTIALS` secret in your GitHub repository (Settings → Secrets → Actions).

- `ACR_LOGIN_SERVER` — your ACR login server, e.g. `myregistry.azurecr.io`.
- `ACR_USERNAME` and `ACR_PASSWORD` — credentials for the ACR. You can get them with:

```bash
az acr credential show --name <ACR_NAME> --query "{username:username,passwords:passwords[0].value}"
```

- `RESOURCE_GROUP` — the Azure resource group containing your Web App.
- `WEBAPP_NAME` — the Azure Web App name (Linux web app configured for container).

How it works
1. On push to `main` the workflow logs in to Azure using `AZURE_CREDENTIALS`.
2. It builds the Docker image and pushes it to your ACR with a tag based on the commit SHA.
3. It calls `az webapp config container set` to point your Web App to the new image and restarts the app.

Notes and tips
- Make sure your Web App is created as a Linux Web App configured to use a custom container. The app must have permissions to pull from your ACR (you can grant pull access via `az role assignment` or use admin-enabled credentials).
- If you prefer to deploy to Azure App Service using the Publish Profile instead of ACR, you can replace the `az` steps with `azure/webapps-deploy` and the `PUBLISH_PROFILE` secret.
