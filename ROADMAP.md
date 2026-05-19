# comparit Roadmap

This roadmap tracks practical next steps before using `comparit` with real
participants, plus likely follow-on work after a pilot.

## Gerneric App Dev Next Steps
- [x] Add a `shuffle` selection algorithm while keeping `random` available.

- [x] Document a plug-and-play pair selector API so future algorithms can use
      participant/session history, global database history, or image metadata.

- [x] Add token revocation.

- [x] Bind participant tokens to a client-side browser session id and preserve that session id in durable browser storage so a token cannot be reused from a different browser/session.

- [x] Add a landing or message page for when a token is presented with a mismatched or lost session id, explaining why the token cannot continue and what next steps the participant should take.

- [x] Token inspection script. You need to see which links are unused, in progress, completed, expired, or consented. This is operational, not study-specific.

- [x] Reset/cleanup script. You need a safe way to clear demo/test responses and tokens before launch. Should require --yes.

- [x] Richer export. Current export is response rows only. It should include token status, consent timestamp, completion timestamp, expiry, and response count or produce a second tokens.csv.

- [x] Preflight script
    One command that checks:
    config loads
    DB initializes
    image root exists
    at least two valid images
    token settings make sense
    export directory is writable

- [x] No-cache headers. Participant pages/API responses should not be cached in awkward ways, especially completed/expired token states.

- [x] Production docs. A minimal nginx/Caddy/systemd example or at least a clear “run behind reverse proxy with HTTPS” note.

## Launch-Critical in Production for Specific Instances

- Add production deployment notes for nginx/apache/Caddy reverse proxy use.
- Document a production server command without `--reload`.
- Confirm `app.base_url` is set to the public HTTPS URL before generating links.
- Add a token inspection script, for example `scripts/list_tokens.py`, showing:
  token status, expiry, consent timestamp, completion timestamp, and response count.
- Add a study reset script with an explicit `--yes` flag for clearing local test
  tokens and responses before a real run.
- Expand CSV export to include token metadata alongside response rows.
- Add image preflight checks for image root existence, readable files, and at
  least two valid images.
- Add no-cache headers for participant-facing pages and API responses.
- Decide and document how incomplete sessions should be handled in analysis.

## Pilot Checklist

- Replace demo text in `config.toml` with the real project context and consent.
- Point `images.image_root` at the real study images.
- Run `python scripts/index_images.py` and confirm the expected image count.
- Generate a small batch of pilot links.
- Complete pilot sessions from multiple browsers or devices.
- Export responses and inspect token status, response counts, and timing values.
- Verify completed and expired token pages look correct.

## Data Quality

- Add optional pair-repeat prevention within a participant session.
- Add a balanced pair selector strategy.
- Expose pair selector configuration in `config.toml`.
- Record user-agent and coarse client metadata only if ethically appropriate and
  disclosed in consent text.
- Add export filters for completed-only, all, and incomplete sessions.

## Operations

- Add systemd service examples.
- Add database backup guidance.
- Add a simple health/preflight command for deployment checks.
- Add documentation for generating new token batches while the app is running.
- Add token revocation support for accidental or contaminated links.

## Later Features

- Replace placeholder image indexing with persisted image records.
- Add admin pages for token status and exports.
- Add optional study progress indicators.
- Support multiple studies/config profiles from one deployment.
- Add pluggable pair-selection modules beyond the built-in random selector.
- Add packaging/release metadata once the public API settles.
