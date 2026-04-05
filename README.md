# bones

A database and API of human bone images and metadata. 56 of 65 bones have images sourced from Wikimedia Commons (Gray's Anatomy illustrations and Wikipedia).

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

Sources images from Wikimedia Commons (Gray's Anatomy illustrations and Wikipedia article images).

## Project structure

```
bones/
├── bones/
│   ├── app.py        # Flask API
│   ├── catalog.py    # Bone metadata (65 bones)
│   └── download.py   # Image downloader
└── images/           # Downloaded bone images
```
