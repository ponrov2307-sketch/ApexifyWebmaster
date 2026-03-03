# Deploy Guide (Web + Bot)

## 1) Prepare secrets
1. Copy `.env.example` to `.env`.
2. Fill all required values.
3. Generate a long random `NICEGUI_STORAGE_SECRET`.
4. Keep `AUTH_MODE=shared_passcode` in production and set `AUTH_SHARED_PASSCODE`.

## 2) Run locally
Web:
```bash
python run_web.py
```

Bot:
```bash
python run_bot.py
```

Docker web:
```bash
docker build -t apexify .
docker run --env-file .env -p 8080:8080 apexify
```

Docker bot:
```bash
docker run --env-file .env apexify python run_bot.py
```

## 3) Railway
1. Create service `apexify-web` from this repo.
2. Set start command to `python run_web.py`.
3. Set all env vars from `.env.example`.
4. Create second service `apexify-bot` from same repo.
5. Set start command to `python run_bot.py`.
6. Copy same env vars.

`railway.toml` is included for the web defaults.

## 4) Render
Use included `render.yaml` blueprint.

It creates:
- `apexify-web` (web service): `python run_web.py`
- `apexify-bot` (worker): `python run_bot.py`

Set environment variables in Render dashboard for both services.
