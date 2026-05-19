# Study Assets

Place optional non-stimulus files here, such as institutional logos.

These assets are served from `/assets/...` and are intentionally separate from
the configured comparison image directory.

For example:

```text
data/assets/logos/institution-logo.svg
```

Then configure:

```toml
[assets]
asset_root = "data/assets"
institution_logo = "logos/institution-logo.svg"
institution_logo_alt = "Institution logo"
```
