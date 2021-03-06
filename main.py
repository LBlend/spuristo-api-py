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
    "time" timestamp NOT NULL,
    devices smallint NOT NULL,
    prediction_people smallint,
    actual_people smallint,
    PRIMARY KEY ("time"),
    CONSTRAINT no_negative_values CHECK (devices >= 0 AND prediction_people >= 0 AND actual_people >= 0)
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


@app.post("/insert", status_code=201, response_model=DeviceLogPoint)
async def insert_datapoint(datapoint: DeviceLogPoint) -> DeviceLogPoint:
    """Insert a new datapoint into the database. Time will be rounded down to the nearest 5th minute"""

    datapoint.time = round_time(datapoint.time)
    datapoint_tuple = tuple(i[1] for i in tuple(datapoint))  # Fetch only the values from request body

    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO device_log (time, devices, prediction_people, actual_people) VALUES (%s, %s, %s, %s)",
            datapoint_tuple,
        )
    except psycopg2.errors.UniqueViolation:
        connection.rollback()
        raise HTTPException(status_code=409, detail="Entry at this timestamp, when rounded down, already exists")
    except psycopg2.errors.NumericValueOutOfRange:
        connection.rollback()
        raise HTTPException(status_code=400, detail="Make sure all numbers of devices and people do not exceed 32767")
    except psycopg2.errors.CheckViolation:
        connection.rollback()
        raise HTTPException(status_code=400, detail="No negative values allowed!")
    else:
        connection.commit()
    finally:
        cursor.close()

    return datapoint.dict()


@app.post("/insert-raw", status_code=201, response_model=DeviceLogPoint)
async def insert_raw_datapoint(datapoint: DeviceLogPoint) -> DeviceLogPoint:
    """Insert raw datapoint, without any rounding of time"""

    datapoint_tuple = tuple(i[1] for i in tuple(datapoint))  # Fetch only the values from request body

    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO device_log (time, devices, prediction_people, actual_people) VALUES (%s, %s, %s, %s)",
            datapoint_tuple,
        )
    except psycopg2.errors.UniqueViolation:
        connection.rollback()
        raise HTTPException(status_code=409, detail="Entry at this timestamp already exists")
    except psycopg2.errors.NumericValueOutOfRange:
        connection.rollback()
        raise HTTPException(status_code=400, detail="Make sure all numbers of devices and people do not exceed 32767")
    except psycopg2.errors.CheckViolation:
        connection.rollback()
        raise HTTPException(status_code=400, detail="No negative values allowed!")
    else:
        connection.commit()
    finally:
        cursor.close()

    return datapoint.dict()


@app.post("/insert-real", status_code=204)
async def insert_real_people(actual_people: int):
    """Insert actual people count into at the current point of time"""

    time = round_time(datetime.utcnow())

    cursor = connection.cursor()
    try:
        cursor.execute("UPDATE device_log SET actual_people = %s WHERE time = %s", (actual_people, time))
        update_successful = True if cursor.rowcount > 0 else False
    except psycopg2.errors.NumericValueOutOfRange:
        connection.rollback()
        raise HTTPException(status_code=400, detail="Actual people count cannot exceed 32767 people")
    except psycopg2.errors.CheckViolation:
        connection.rollback()
        raise HTTPException(status_code=400, detail="No negative values allowed!")
    else:
        connection.commit()
    finally:
        cursor.close()

    if not update_successful:
        raise HTTPException(status_code=404, detail="No entry found at this timestamp")


@app.get("/latest", response_model=DeviceLogPoint)
async def get_latest_datapoint() -> DeviceLogPoint:
    """Get the latest datapoint from the database"""

    cursor = connection.cursor()
    cursor.execute("SELECT * FROM device_log ORDER BY time DESC LIMIT 1")
    data = cursor.fetchone()
    cursor.close()

    if data:
        return DeviceLogPoint(time=data[0], devices=data[1], prediction_people=data[2], actual_people=data[3])
    raise HTTPException(status_code=404, detail="No entries in database")


@app.get("/training", response_model=list[DeviceLogPoint])
async def get_training_datapoints() -> list[DeviceLogPoint]:
    """Get all datapoints that contains a human labeled number of actual people"""

    cursor = connection.cursor()
    cursor.execute("SELECT * FROM device_log WHERE actual_people IS NOT NULL")
    data = cursor.fetchall()
    cursor.close()

    if data:
        return [DeviceLogPoint(time=i[0], devices=i[1], prediction_people=i[2], actual_people=i[3]) for i in data]
    return []


@app.get("/all", response_model=list[DeviceLogPoint])
async def get_all_datapoints() -> list[DeviceLogPoint]:
    """Get all datapoints from the database"""

    cursor = connection.cursor()
    cursor.execute("SELECT * FROM device_log")
    data = cursor.fetchall()
    cursor.close()

    if data:
        return [DeviceLogPoint(time=i[0], devices=i[1], prediction_people=i[2], actual_people=i[3]) for i in data]
    return []


@app.delete("/delete", status_code=204)
async def delete_datapoint(unix_timestamp: datetime):
    """Delete a specified datapoint from the database"""

    cursor = connection.cursor()
    cursor.execute("DELETE FROM device_log WHERE time = %s", (unix_timestamp,))
    delete_successful = True if cursor.rowcount > 0 else False
    cursor.close()

    if not delete_successful:
        raise HTTPException(status_code=404, detail="No entry found at this timestamp")


@app.delete("/delete-current-latest", status_code=204)
async def delete_current_latest_datapoint():
    """Delete the latest datapoint, if there is any rounded down to nearest 5th minute, from the database"""

    time = round_time(datetime.utcnow())

    cursor = connection.cursor()
    cursor.execute("DELETE FROM device_log WHERE time = %s", (time,))
    delete_successful = True if cursor.rowcount > 0 else False
    cursor.close()

    if not delete_successful:
        raise HTTPException(status_code=404, detail="No entry found at this timestamp")
