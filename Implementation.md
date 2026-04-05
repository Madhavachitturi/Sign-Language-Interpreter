# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment

Always use the venv Python interpreter, **not** the system Python:

```bash
venv/Scripts/python <script.py>
venv/Scripts/pip install <package>
```

The venv uses **Python 3.10.11** with **scikit-learn 1.2.0**. scikit-learn 1.8.0+ requires Python ≥3.11 and is incompatible with this environment.

## Pipeline — Run in Order

```bash
venv/Scripts/python collect_imgs.py       # Step 1: capture webcam images to ./data/
venv/Scripts/python create_dataset.py     # Step 2: extract landmarks → data.pickle
venv/Scripts/python train_classifier.py   # Step 3: train model → model.p
venv/Scripts/python inference_classifier.py  # Step 4: real-time webcam inference
```

Steps 1–3 only need to be re-run when the training data changes. **model.p must be retrained with the same sklearn version used at inference** — a version mismatch causes a hard `ValueError` crash at startup.

## Architecture

The pipeline is a 4-script sequential workflow:

1. **`collect_imgs.py`** — Opens webcam, collects 100 images per class into `./data/<class_index>/`. 26 classes (0–25 → A–Z). Press `Q` to start capturing each class.

2. **`create_dataset.py`** — Reads images from `./data/`, runs MediaPipe hand detection (`max_num_hands=1`, `min_detection_confidence=0.3`), extracts 21 hand landmarks (x, y each), normalizes them relative to `min(x_)` / `min(y_)`, and pickles the result to `data.pickle`.

3. **`train_classifier.py`** — Loads `data.pickle`, trains a `RandomForestClassifier` (default hyperparameters), evaluates on a 20% test split, and saves the model to `model.p`.

4. **`inference_classifier.py`** — Loads `model.p`, opens webcam in a loop, runs the same MediaPipe landmark extraction as `create_dataset.py`, feeds the feature vector to the model, and draws the predicted letter + bounding box on the frame.

## Feature Vector Format

Each sample is a flat list of 42 floats: `[x0−min_x, y0−min_y, x1−min_x, y1−min_y, ..., x20−min_x, y20−min_y]` — the 21 MediaPipe hand landmarks normalized to the hand's bounding box origin. **`create_dataset.py` and `inference_classifier.py` must use identical normalization logic**, otherwise predictions will be wrong.

## Known Constraints

- **Single hand only** — `create_dataset.py` uses `max_num_hands=1` but `inference_classifier.py` uses the default (2 hands). If two hands are detected at inference, `data_aux` will have 84 features instead of 42, causing a model prediction error.
- `dataset_size` in `collect_imgs.py` is hardcoded to 100 images/class. Change it there before collecting.
