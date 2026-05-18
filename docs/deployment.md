# Deployment Notes

These notes describe a small production-style deployment for `comparit`.

## Assumptions

- Run `comparit` on a server you control.
- Put a reverse proxy such as nginx, Apache, or Caddy in front of Uvicorn.
- Serve the public site over HTTPS.
- Keep the SQLite database on a normal local disk, not a network filesystem.
- Do not use `--reload` in production.

## Before Launch

Edit `config.toml`:

```toml
[app]
base_url = "https://your-public-site.example"

[images]
image_root = "/absolute/path/to/study/images"
```

Run:

```bash
conda activate comparit
python scripts/init_db.py
python scripts/preflight.py
```

Only generate participant links after `base_url` is correct:

```bash
python scripts/generate_tokens.py --count 25
```

## Manual Production Command

Run Uvicorn bound to localhost:

```bash
conda activate comparit
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The reverse proxy should forward public HTTPS traffic to
`http://127.0.0.1:8000`.

## Example systemd Unit

Adjust paths and user names before use.

```ini
[Unit]
Description=comparit pairwise comparison app
After=network.target

[Service]
Type=simple
User=YOUR_USER
WorkingDirectory=/path/to/comparit
ExecStart=/path/to/miniconda3/envs/comparit/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## Example nginx Location

This assumes TLS is already configured for the server block.

```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

## Operations

Inspect token status:

```bash
python scripts/list_tokens.py
```

Export data:

```bash
python scripts/export_results.py
```

Back up at least:

```text
config.toml
data/comparit.sqlite3
exports/
```

When SQLite WAL mode is active, temporary `data/comparit.sqlite3-wal` and
`data/comparit.sqlite3-shm` files may exist while the app is running. Stop the
app before making a simple file-copy backup.
