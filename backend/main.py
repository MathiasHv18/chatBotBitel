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
    lib_dir=r"C:\oracle\instantclient-basic-windows.x64-23.7.0.25.01\instantclient_23_7")


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


def get_all_database_info(max_tables=50):

    conn = get_oracle_connection()
    if not conn:
        return "Failed to connect to the database"

    table_names = get_all_table_names(conn)

    # Limit number of tables to process
    if len(table_names) > max_tables:
        print(
            f"Limiting to {max_tables} tables out of {len(table_names)} total tables")
        table_names = table_names[:max_tables]

    database_info = []

    for table_name in table_names:
        try:
            sample_df = get_table_data(conn, table_name)

            if not sample_df.empty:
                table_info = {
                    "table_name": table_name,
                    "sample": sample_df.to_markdown(index=False) if not sample_df.empty else "No data available"
                }
                database_info.append(table_info)
        except Exception as e:
            print(f"Error processing table {table_name}: {e}")

    conn.close()

    return database_info


class QueryRequest(BaseModel):
    prompt: str


@app.post("/api/query_database")
async def query_database(request: QueryRequest):
    print("Received request:", request)  # Agrega este log
    # Get database information
    print("Getting database information...")
    database_info = get_all_database_info(max_tables=30)

    # Format the database information for the LLM

    # Create system message with database context
    print("Creating system message...")
    system_message = """
This GPT acts as a data analyst specialized in churn prediction analysis for telecommunications company customers. It works with multiple datasets related to customer activity, refills, complaints, consumption details, payments, discounts, packages, customer demographics, and product offers.
        """

    # Create user message with the formatted database info and user prompt
    user_message = f"""
        {database_info}
        
        Pregunta del usuario: {request.prompt}
        """

    print("User prompt", request.prompt)

    # Call OpenAI API with retry logic
    max_retries = 3
    retry_count = 0
    backoff_time = 1

    while retry_count < max_retries:
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Use a model with larger context
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=1000
            )
            return {"response": response.choices[0].message.content.strip()}
        except openai.RateLimitError:
            retry_count += 1
            if retry_count < max_retries:
                time.sleep(backoff_time)
                backoff_time *= 2
            else:
                return {"error": "OpenAI API rate limit exceeded. Please try again later."}
        except Exception as e:
            return {"error": f"Error calling OpenAI API: {str(e)}"}


@app.get("/")
async def root():
    return {"message": "API is working!"}
