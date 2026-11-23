# Identify The Image

Upload a photo and the app tells you whether it shows a **cat** or a **dog** (or neither).

A small test app for deploying with DeployPilot: one FastAPI service in one Docker container.

## How it works

- A pre-trained image model, **MobileNetV2** (ONNX, 14 MB, in `backend/models/`), looks at the photo.
  It knows 1000 kinds of things from ImageNet; 118 of them are dog breeds and 5 are house cats.
- The chance of "dog" is the sum over the dog breeds, of "cat" over the cats. If neither reaches
  `MIN_CONFIDENCE` (default 0.5), the answer is "neither".
- No API key and no outside service. Photos are not stored.

## Folder structure

```
backend/                FastAPI server (Python)
  app/
    main.py             creates the app, serves the frontend
    config.py           paths and settings from the environment
    api/routes.py       /health and /api/predict
    services/classifier.py   the image model
  models/               MobileNetV2 ONNX file + ImageNet labels
  tests/                pytest tests (photos go in tests/photos/)
  requirements.txt      runtime packages
  requirements-dev.txt  + test packages
frontend/               the web page (plain HTML, CSS, JS)
  index.html
  assets/css/style.css
  assets/js/app.js
Dockerfile              builds one container with both
pytest.ini              lets `pytest -q` run from the repo root
```

| Path | What |
|---|---|
| `GET /` | The web page |
| `GET /assets/...` | The page's CSS and JavaScript |
| `GET /health` | `{"status": "ok"}` (health check) |
| `POST /api/predict` | Form field `photo` → `{"label": "cat"\|"dog"\|"neither", "confidence", "cat", "dog", "best_guess"}` |

## Run it on your PC

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows (macOS/Linux: source .venv/bin/activate)
pip install -r backend/requirements-dev.txt
cd backend
uvicorn app.main:app --reload     # http://127.0.0.1:8000
cd ..
pytest -q                         # tests (from the repo root)
```

With Docker:

```bash
docker build -t identify-the-image .
docker run -p 8000:8000 identify-the-image   # http://localhost:8000
```

To also test with real photos, put files named like `cat1.jpg` or `dog1.png` in `backend/tests/photos/`
(git-ignored) and run `pytest -q`.

## Settings (optional)

See `.env.example`. In DeployPilot, set them under Project → Settings → Environment variables.

| Name | Default | Meaning |
|---|---|---|
| `MAX_UPLOAD_MB` | 5 | Biggest photo accepted (1-20 MB) |
| `MIN_CONFIDENCE` | 0.5 | How sure the model must be to say cat or dog (0.05-0.95) |

## Deploying with DeployPilot

DeployPilot should detect: Python / FastAPI, the Dockerfile, port **8000**, health check
**/health**, test command `pytest -q`, 2 environment variable names, and recommend
**EC2 instance + Elastic IP**. The container needs about 100 MB of memory.

## Credits

Model: MobileNetV2 from the [ONNX Model Zoo](https://github.com/onnx/models) (Apache 2.0).
Labels: ImageNet class names from [pytorch/hub](https://github.com/pytorch/hub).
