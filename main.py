from dotenv import load_dotenv
from fastapi import FastAPI
from os import getenv
import psycopg2


app = FastAPI()


load_dotenv()
connection = psycopg2.connect(
    host=getenv("DB_HOST"),
    database=getenv("DB_NAME"),
    user=getenv("DB_USER"),
    password=getenv("DB_PASSWORD"),
)


# Create database tables
create_query = """
CREATE TABLE IF NOT EXISTS public.device_log
(
    "time" timestamp with time zone NOT NULL,
    devices smallint NOT NULL,
    prediction_people smallint,
    actual_people smallint,
    PRIMARY KEY ("time")
);

ALTER TABLE public.device_log
    OWNER to %s;
"""
cursor = connection.cursor()
cursor.execute(create_query % getenv("DB_USER"))
connection.commit()
cursor.close()


@app.get("/")
async def root():
    return "Pog yeet yeet"


@app.post("/insert")
async def insert_datapoint(data: dict):
    cur = connection.cursor()
    cur.execute("INSERT INTO training_data time, devices, prediction_people, actual_people VALUES (%s)", (data,))
    connection.commit()
    cur.close()
    return {"success": True}


@app.get("/latest")
async def get_latest_datapoint():
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM device_log ORDER BY time DESC LIMIT 1")
    data = cursor.fetchone()
    cursor.close()
    return data[0]


@app.get("/training")
async def get_training_datapoints():
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM device_log WHERE actual_people != null")
    data = cursor.fetchall()
    cursor.close()
    return data


@app.get("/all")
async def get_all_datapoints():
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM device_log")
    data = cursor.fetchall()
    cursor.close()
    return data
