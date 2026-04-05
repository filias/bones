# bones

A database and API of human bone images and metadata. All 65 bones have images.

## Run

```
uv run python -m bones
```

Then open http://localhost:8081

## API

| Endpoint | Description |
|---|---|
| `GET /bones` | List all bones (optional `?region=` filter) |
| `GET /bones/<id>` | Get a specific bone |
| `GET /bones/random` | Random bone (optional `?region=`, `?has_image=true`) |
| `GET /regions` | List all body regions |
| `GET /images/<filename>` | Serve a bone image |

## Download images

```
uv run python -m bones.download
```

Use `--force` to re-download all images.

## Image sources and attribution

Images are sourced from (in order of preference):

1. **[eSkeletons.org](https://www.eskeletons.org/)** — photographs by John Kappelman and the University of Texas at Austin, licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)
2. **Wikimedia Commons** — Gray's Anatomy illustrations (public domain)
3. **Wikipedia** — article images (various licenses)

eSkeletons images are used for non-commercial, educational purposes with attribution as required by their license.

## Project structure

```
bones/
├── bones/
│   ├── app.py        # Flask API
│   ├── catalog.py    # Bone metadata (65 bones)
│   └── download.py   # Image downloader
└── images/           # Downloaded bone images (gitignored)
```
