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
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cx_Oracle.init_oracle_client(
    lib_dir=r"C:\oracle\instantclient-basic-windows.x64-23.7.0.25.01\instantclient_23_7")

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


def get_all_table_names(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT table_name FROM user_tables ORDER BY table_name")
    table_names = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return table_names


def get_table_metadata(conn, table_name):
    cursor = conn.cursor()
    query = """
        SELECT COLUMN_NAME, DATA_TYPE
        FROM USER_TAB_COLUMNS
        WHERE TABLE_NAME = :table_name
    """
    cursor.execute(query, {"table_name": table_name})
    metadata = {row[0]: row[1] for row in cursor.fetchall()}
    cursor.close()
    return metadata


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
    """
    Get metadata and sample data for all tables in the database.
    Limit to max_tables to prevent overwhelming the API.
    """
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
            metadata = get_table_metadata(conn, table_name)
            sample_df = get_table_data(conn, table_name)

            if not sample_df.empty:
                table_info = {
                    "table_name": table_name,
                    "columns": metadata,
                    "sample": sample_df.to_markdown(index=False) if not sample_df.empty else "No data available"
                }
                database_info.append(table_info)
        except Exception as e:
            print(f"Error processing table {table_name}: {e}")

    conn.close()

    return database_info


def format_database_info(database_info):
    """Format the database info into a readable string for the LLM"""
    formatted_info = "DATABASE SCHEMA INFORMATION:\n\n"

    for table_info in database_info:
        formatted_info += f"TABLE: {table_info['table_name']}\n"
        formatted_info += "COLUMNS:\n"
        for col, dtype in table_info['columns'].items():
            formatted_info += f"- {col}: {dtype}\n"

        formatted_info += "\nSAMPLE DATA:\n"
        formatted_info += table_info['sample'] + "\n\n"
        formatted_info += "-" * 50 + "\n\n"

    return formatted_info


class QueryRequest(BaseModel):
    prompt: str


@app.post("/api/query_database")
async def query_database(request: QueryRequest):
    try:
        # Get database information (limited to 10 tables to avoid context issues)
        database_info = get_all_database_info(max_tables=30)

        if isinstance(database_info, str):  # Error occurred
            return {"error": database_info}

        # Format the database information for the LLM
        formatted_db_info = format_database_info(database_info)

        # Create system message with database context
        system_message = """
        Eres un asistente de SQL experto en análisis de bases de datos. 
        Te han proporcionado información sobre el esquema de la base de datos.
        Utiliza esta información para responder a las preguntas del usuario.
        Si necesitas consultar datos específicos, sugiere la consulta SQL adecuada.
        """

        # Create user message with the formatted database info and user prompt
        user_message = f"""
        {formatted_db_info}
        
        Pregunta del usuario: {request.prompt}
        """

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

    except Exception as e:
        return {"error": f"Server error: {str(e)}"}


@app.get("/api/table_names")
async def get_table_names_endpoint():
    """Returns the list of tables available in the database"""
    conn = get_oracle_connection()
    if not conn:
        return {"error": "Failed to connect to the database"}

    table_names = get_all_table_names(conn)
    conn.close()
    return {"table_names": table_names}
