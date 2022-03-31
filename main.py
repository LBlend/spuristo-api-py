from fastapi import FastAPI
from os import getenv
import psycopg2


app = FastAPI()

connection = psycopg2.connect(
    host=getenv('DB_HOST'),
    database=getenv('DB_NAME'),
    user=getenv('DB_USER'),
    password=getenv('DB_PASSWORD'),
)


@app.get("/")
async def root():
    return "Pog yeet yeet"
