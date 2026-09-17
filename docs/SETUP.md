# Setup Guide

This document explains how to set up the project locally and run the research workflow.

## 1. Requirements

- Python 3.10+
- Docker
- local SearXNG instance
- access to a model provider (Hugging Face is the current default)

---

## 2. Environment creation

```bash
cd /workspaces/Tool-Use
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

If the project is managed with `uv`, the environment may also be initialized with the project configuration in `pyproject.toml`.

---

## 3. Environment variables

Copy the sample environment file:

```bash
cp .env.example .env
```

Then configure the keys in `.env`:

```env
SEARXNG_BASE_URL=http://localhost:8080
SEARXNG_SECRET=
HUGGINGFACE_HUB_TOKEN=your_token_here
LLM_MODEL_NAME=mistralai/Mistral-7B-Instruct-v0.3
```

---

## 4. Start the search backend

```bash
docker compose up -d searxng
```

Then verify that the service is reachable:

```bash
curl "http://localhost:8080/search?q=python&format=json"
```

---

## 5. Run the app

```bash
python main.py
```

You will be prompted to enter a research question. The orchestrator will:

- build a plan,
- search the web,
- retrieve sources,
- summarize the evidence,
- save run artifacts.

---

## 6. Run validation tests

```bash
cd /workspaces/Tool-Use
source .venv/bin/activate
python -m pytest -q tests/test_refactor.py
```

This is the active validation path for the current implementation.
