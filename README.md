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

2. Rename the [.env.example](.env.example) file to `.env` and enter your database details

3. Run the API

```
uvicorn main:app --reload
```

The API will now be available at [http://127.0.0.1:8000](http://127.0.0.1:8000), assuming you haven't changed the port.

The docs can be found at [/docs](http://127.0.0.1:8000/docs)

![image illustrating how the docs page looks](https://user-images.githubusercontent.com/24893890/163731941-162de9e4-784f-47e2-a782-4ce7188f853b.png)

