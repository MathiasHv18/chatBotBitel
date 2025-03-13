from fastapi import FastAPI
import cx_Oracle
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import dotenv
import os

openai.api_key = os.getenv("ApiKey")
app = FastAPI()

# Cors allow *
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Server frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Table(BaseModel):
    id: int
    name: str
    recordCount: int


# Change in production
cx_Oracle.init_oracle_client(
    lib_dir=r"C:\oracle\instantclient-basic-windows.x64-23.7.0.25.01\instantclient_23_7")

# Change in production
DB_CONFIG = {
    "username": "training_ai",
    "password": "Bitel*123",
    "host": "181.176.39.55",
    "port": 1521,
    "service_name": "stage"
}

dsn = cx_Oracle.makedsn(
    DB_CONFIG["host"], DB_CONFIG["port"], service_name=DB_CONFIG["service_name"])


def get_oracle_connection():
    try:
        conn = cx_Oracle.connect(
            DB_CONFIG["username"], DB_CONFIG["password"], dsn)
        print("Connected to Oracle Database")
        return conn
    except cx_Oracle.DatabaseError as e:
        print(f"Database connection error: {e}")
        return None


def getImportantSite(conn):
    cursor = conn.cursor()
    query = 'select * from test_10K_isdn_age'
    cursor.execute(query)
    listSites = cursor.fetchall()
    cursor.close()
    return listSites


@app.get("/api/test")
async def get_site_conf():
    conn = get_oracle_connection()
    if not conn:
        return {"error": "Could not connect to Oracle DB"}

    df = getImportantSite(conn)
    conn.close()

    return df
