# comparit

`comparit` is a lightweight FastAPI web app for pairwise image comparison
experiments. It is designed for small scientific or academic studies where
participants receive unique links, accept consent text, compare image pairs,
and then finish the task.

The app currently supports:

- Configurable project/branding/consent text in `config.toml`
- Tokenized participant links
- Token expiry and completion states
- Random image-pair selection
- Optional skip and tie responses
- Response-time capture
- SQLite storage
- CSV export
- A bundled demo image set for local testing

## 1. First-Time Setup

From the project directory:

```bash
conda env create -f environment.yml
conda activate comparit
cp config.example.toml config.toml
python scripts/init_db.py
python scripts/index_images.py
```

The example config uses the bundled demo images in:

```text
data/demo_images/cats
```

## 2. Development Launch

For local development, use the helper script:

```bash
conda activate comparit
./launch_dev.sh
```

This script will:

- initialize the SQLite database
- check the configured image directory
- generate a one-off local development token
- start the FastAPI development server
- open a tokenized participant link in your browser

Stop the dev server with `Ctrl+C`.

Useful variants:

```bash
./launch_dev.sh --no-browser
./launch_dev.sh --port 8765
./launch_dev.sh --no-reload
./launch_dev.sh --token EXISTING_TOKEN
```

## 3. Production-Style Manual Launch

Before generating real participant links, edit [config.toml](config.toml).

Most important:

```toml
[app]
base_url = "https://your-public-site.example"

[images]
image_root = "/absolute/path/to/your/study/images"
```

Initialize/check the app:

```bash
conda activate comparit
python scripts/init_db.py
python scripts/index_images.py
```

Start the app without reload:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

For an actual public deployment, run this behind a reverse proxy such as nginx,
Apache, or Caddy, and expose the public site over HTTPS. Do not use
`--reload` in production. See [docs/deployment.md](docs/deployment.md) for a
systemd example and reverse proxy notes.

## 4. Generate Participant Links

New links can be generated while the app is already running. No restart is
needed.

Make sure `base_url` in `config.toml` is correct first. Then run:

```bash
conda activate comparit
python scripts/generate_tokens.py --count 25
```

The script stores tokens in SQLite and prints links like:

```text
https://your-public-site.example/?t=<token>
```

Send one link to each participant.

Token behavior:

- New tokens start as `unused`.
- Opening a link moves the token to `in_progress`.
- Participants must accept the consent screen before image pairs load.
- Consent acceptance binds the token to that browser session.
- When `comparisons_per_session` responses are recorded, the token becomes
  `completed`.
- Completed tokens cannot be reused.
- Tokens opened later from another browser/session show the configured session
  mismatch message.
- Expired tokens show the configured expiry message.
- Tokens can be revoked manually if a link should no longer be usable.

Revoke a token with:

```bash
python scripts/revoke_token.py TOKEN_STRING
```

## 5. Export Data

Export captured responses and token metadata with:

```bash
conda activate comparit
python scripts/export_results.py
```

The CSV files are written to:

```text
exports/comparison_responses.csv
exports/participant_tokens.csv
```

`comparison_responses.csv` includes response rows with:

- participant token id
- browser session id
- left image id
- right image id
- selected image id
- action: `select`, `tie`, or `skip`
- pair selection strategy
- response time in milliseconds
- timestamp

`participant_tokens.csv` includes token status, effective status, consent
timestamp, expiry timestamp, completion timestamp, and response count.

## 6. Inspect Tokens

List participant links and their operational status with:

```bash
conda activate comparit
python scripts/list_tokens.py
```

The output shows token id, effective status, response count, consent state,
creation time, expiry time, and token string.

## 7. Run Preflight Checks

Before generating real links, run:

```bash
conda activate comparit
python scripts/preflight.py
```

This checks that configuration loads, the database initializes, the image root
exists, at least two images are available, token settings are positive, and the
export directory is writable.

## 8. Reset Local Study Data

To clear participant tokens, sessions, and responses before a real launch:

```bash
conda activate comparit
python scripts/reset_study_data.py --yes
```

This does not delete image files or `config.toml`. The `--yes` flag is required
on purpose.

## 9. Configuration Reference

The main study settings live in [config.toml](config.toml):

```toml
[app]
name = "comparit"
debug = true
base_url = "http://127.0.0.1:8000"

[database]
path = "data/comparit.sqlite3"

[experiment]
project_title = "Demo Cat Image Comparison"
project_context = "This short demo asks you to compare simple cat images so the comparit workflow can be tested locally."
institution_name = "Example Research Group"
institution_branding = "Open visual comparison study"
consent_text = "I understand that this demo records my image choices and response times. I understand that I can stop participating by closing the browser tab."
completion_text = "Thank you for completing this demo comparison task. Your responses have been recorded."
token_expired_text = "This experiment link has expired. Please contact the study organizer if you believe this is an error."
session_mismatch_text = "This experiment link is already associated with another browser session. Please return to the original browser, or contact the study organizer for a new link."
instructions = "Select the cat image that feels more relaxed."
allow_skip = true
allow_tie = false
pair_selection_strategy = "random"
token_required = true
comparisons_per_session = 20
token_validity_days = 28
in_progress_expiry_minutes = 1440

[images]
image_root = "data/demo_images/cats"
allowed_extensions = [".jpg", ".jpeg", ".png", ".webp", ".svg"]

[exports]
output_dir = "exports"
```

## 10. Useful Checks

Run tests and linting:

```bash
conda activate comparit
ruff check .
pytest
```

Check image discovery:

```bash
python scripts/index_images.py
```

Check that the database file exists:

```bash
ls -lh data/comparit.sqlite3
```

Inspect tables without the external `sqlite3` CLI:

```bash
python -m sqlite3 data/comparit.sqlite3 \
  "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
```

## 11. Project Layout

```text
app/
  core/          Configuration and shared helpers.
  db/            SQLite connections, schema, responses, and tokens.
  routes/        FastAPI routes and JSON APIs.
  services/      Image discovery, token generation, pair selection.
  static/        CSS and vanilla JavaScript.
  templates/     Server-rendered HTML templates.
scripts/         Local setup, launch, token, and export scripts.
data/            Local SQLite database and demo images.
exports/         CSV export output.
docs/            Project notes.
tests/           Automated tests.
```

## 12. Notes

The bundled cat images are simple SVG fixtures for local testing. Replace
`images.image_root` with your real study image directory before launch.

SQLite is configured with WAL mode and a busy timeout. This is appropriate for
small studies with a few dozen raters, provided the database is stored on a
normal local disk.

See [ROADMAP.md](ROADMAP.md) for remaining launch-critical work and future
features.

See [docs/pair_selectors.md](docs/pair_selectors.md) for the pair selector API
and built-in `random`/`shuffle` strategies.

## License

MIT. See [LICENSE](LICENSE).
