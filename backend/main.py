from fastapi import FastAPI
import cx_Oracle
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import openai
import dotenv
import os
import time
from typing import List, Dict, Any

dotenv.load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cx_Oracle.init_oracle_client(
    lib_dir=r"C:\oracle\instantclient_23_7")


DB_CONFIG = {
    "username": os.getenv("DB_USERNAME"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "service_name": os.getenv("DB_SERVICE_NAME")
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


def get_all_table_names(conn):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT table_name FROM user_tables ORDER BY table_name")
    table_names = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return table_names


def get_specific_table(conn, table_name="TEST_10K_CONSUMPTION"):
    print(f"Getting sample from {table_name}...")
    try:
        cursor = conn.cursor()
        query = f"SELECT * FROM {table_name}"
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        cursor.close()
        return pd.DataFrame(rows, columns=columns)
    except Exception as e:
        print(f"Error getting sample from {table_name}: {e}")
        return pd.DataFrame()


def get_table_data(conn, table_name):
    try:
        cursor = conn.cursor()
        query = f"SELECT * FROM {table_name}"
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        cursor.close()
        return pd.DataFrame(rows, columns=columns)
    except Exception as e:
        print(f"Error getting sample from {table_name}: {e}")
        return pd.DataFrame()


class QueryRequest(BaseModel):
    prompt: str


@app.post("/api/query_database")
async def query_database(request: QueryRequest):
    conn = get_oracle_connection()

    if not conn:
        return "Failed to connect to the database"

    print("Received request:", request)

    # Create system message with database context
    print("Creating system message...")
    system_message = """
    This GPT acts as a data analyst specialized in churn prediction analysis for telecommunications company customers. It works with multiple datasets related to customer activity, refills, complaints, consumption details, payments, discounts, packages, customer demographics, and product offers.
        """

    data = get_specific_table(conn)

    # Create user message with the formatted database info and user prompt
    user_message = f"""
        {data}
        
        Pregunta del usuario: {request.prompt}
        """

    print("User prompt", request.prompt)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Hola"},
                {"role": "user", "content": user_message},
            ],
            max_tokens=1000
        )
        return {"response": response.choices[0].message.content.strip()}
    except openai.RateLimitError:
        return {"error": "OpenAI API rate limit exceeded. Please try again later."}
    except Exception as e:
        return {"error": f"Error calling OpenAI API: {str(e)}"}
    finally:
        conn.close()


@app.get("/")
async def root():
    print(os.getenv("DB_USERNAME"))
    print(os.getenv("DB_PASSWORD"))
    print(os.getenv("DB_HOST"))
    print(os.getenv("DB_PORT"))
    print(os.getenv("DB_SERVICE_NAME"))
    get_oracle_connection()
    return {"message": "API is working!"}
