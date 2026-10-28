# onset-practice-app

Custom app made for practising for the Onset test. Includes 10 new practice tests.

## Requirements

- Python 3 (no extra packages, standard library only)
- Git

## Install

```bash
git clone git@github.com:MatijaRadulovic/onset-practice-app.git
cd onset-practice-app
```

## Run

```bash
python3 app/serve.py
```

Then open http://localhost:8000 in your browser.

Use a different port by passing it as an argument:

```bash
python3 app/serve.py 8080
```

Stop the server with `Ctrl+C`.

## Layout

- `app/` – web UI (`index.html`) and server (`serve.py`)
- `exam-original/`, `exam-01/` … `exam-10/` – practice tests (texts + `answers.md`)
- `tools/` – scripts used to generate/check the tests
