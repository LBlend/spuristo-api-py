from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from os import getenv
import psycopg2
from pydantic import BaseModel


app = FastAPI()

# Load environment variables and connect to database
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


def round_time(time: datetime) -> datetime:
    """Round down to nearest 5th minute"""
    new_minute = time.minute - (time.minute % 5)
    return time.replace(minute=new_minute, second=0, microsecond=0)


class DeviceLogPoint(BaseModel):
    time: datetime
    devices: int
    prediction_people: int | None
    actual_people: int | None


@app.get("/", response_model=str)
async def root() -> str:
    """Endpoint for testing whether the API is running or not"""

    return "Pog yeet yeet"


@app.post("/insert", status_code=201, response_model=DeviceLogPoint)
async def insert_datapoint(datapoint: DeviceLogPoint) -> DeviceLogPoint:
    """Insert a new datapoint into the database. Time will be rounded down to the nearest 5th minute"""
    datapoint_tuple = tuple(i[1] for i in tuple(datapoint))  # Fetch only the values from request body

    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO device_log (time, devices, prediction_people, actual_people) VALUES (%s, %s, %s, %s)",
        datapoint_tuple,
    )
    connection.commit()
    cursor.close()

    return {"success": True, "data": datapoint.dict()}

@app.post("/insert-real", status_code=204, response_model=DeviceLogPoint)
async def insert_real_people(actual_people: int) -> DeviceLogPoint:
    """Insert actual people count into at the current point of time"""

@app.post("/insert_real")
async def insert_real_people(actual_people: int):
    cursor = connection.cursor()
    cursor.execute("UPDATE TABLE device_log SET actual_people VALUES (%s) WHERE time = %s", (actual_people,))
    connection.commit()
    cursor.close()
    return {"success": True}

@app.get("/latest", response_model=DeviceLogPoint)
async def get_latest_datapoint() -> DeviceLogPoint:
    """Get the latest datapoint from the database"""

    cursor = connection.cursor()
    cursor.execute("SELECT * FROM device_log ORDER BY time DESC LIMIT 1")
    data = cursor.fetchone()
    cursor.close()

    return DeviceLogPoint(time=data[0], devices=data[1], prediction_people=data[2], actual_people=data[3])


@app.get("/training", response_model=list[DeviceLogPoint])
async def get_training_datapoints() -> list[DeviceLogPoint]:
    """Get all datapoints that contains a human labeled number of actual people"""

    cursor = connection.cursor()
    cursor.execute("SELECT * FROM device_log WHERE actual_people IS NOT NULL")
    data = cursor.fetchall()
    cursor.close()

    return [DeviceLogPoint(time=i[0], devices=i[1], prediction_people=i[2], actual_people=i[3]) for i in data]


@app.get("/all", response_model=list[DeviceLogPoint])
async def get_all_datapoints() -> list[DeviceLogPoint]:
    """Get all datapoints from the database"""

    cursor = connection.cursor()
    cursor.execute("SELECT * FROM device_log")
    data = cursor.fetchall()
    cursor.close()

    return [DeviceLogPoint(time=i[0], devices=i[1], prediction_people=i[2], actual_people=i[3]) for i in data]
