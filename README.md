# spuristo API - Python edition

This repo contains the API which provides and interface for [spuristo](https://github.com/LBlend/spuristo) to communicate with its database.

The API is written in Python but I'm planning on rewriting this in Rust at some point, hence the name.

## Prerequisites

- Python 3.10+
- A Postgresql database

## Get started

1. Install dependencies

```
python -m pip install -r requirements.txt
```

2. Run the API

```
uvicorn main:app --reload
```
