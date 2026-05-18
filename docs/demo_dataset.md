# Demo Dataset

`data/demo_images/cats` contains a tiny bundled image set for smoke testing.

The images are simple SVG fixtures rather than photographs. That keeps the
repository lightweight, avoids external licensing questions, and makes the
default setup work without downloads.

Use this dataset to verify:

- The configured image root exists.
- `scripts/index_images.py` can discover supported files.
- Future comparison views have local images to display immediately.

For real experiments, copy `config.example.toml` to `config.toml` and point
`images.image_root` at your study image directory.
