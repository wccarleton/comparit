# Architecture Notes

Phase 1 keeps the project deliberately plain.

- `app.main` owns FastAPI application construction.
- `app.routes` owns HTTP routes and template rendering.
- `app.core.config` owns local configuration loading and path normalization.
- `app.db` owns SQLite connections and schema setup.
- `app.services` owns experiment-domain operations that can later be tested
  independently from FastAPI routes.
- `scripts` exposes local maintenance workflows for researchers.

TODO: Add a fuller experiment lifecycle document once image indexing,
assignment, response capture, and exports are implemented.
