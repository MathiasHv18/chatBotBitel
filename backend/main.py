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

# Mantener el historial de mensajes en memoria
conversation_history = [
    {"role": "system", "content": """
    This GPT acts as a data analyst specialized in churn prediction analysis for 
    telecommunications company customers. It works with multiple datasets related 
    to customer activity, refills, complaints, consumption details, payments, 
    discounts, packages, customer demographics, and product offers.
    """}
]


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


class QueryRequest(BaseModel):
    prompt: str


@app.get("/api/send_data_to_openai")
async def send_data_to_openai():
    global conversation_history

    conn = get_oracle_connection()
    if not conn:
        return {"error": "Failed to connect to the database"}

    try:
        print("Sending data to OpenAI...")
        tables = get_all_table_names(conn)
        print("Tables:", tables)

        data_message = "Here is the database information for your analysis:\n\n"

        for table in tables:
            try:
                df = get_table_data(conn, table)
                # Convertir cada tabla a un formato más legible y limitar a las primeras 10 filas
                sample_data = df.head(10).to_string()
                data_message += f"Table {table}:\n{sample_data}\n\n"
                print(f"Data from {table} completed")
            except Exception as e:
                print(f"Error fetching data from {table}: {str(e)}")

        # Agregar los datos al historial de conversación
        conversation_history.append({"role": "user", "content": data_message})

        # Get the response from OpenAI
        response = client.chat.completions.create(
            model="gpt-4.5-preview",
            messages=conversation_history,
            max_tokens=150
        )

        # Save the response in the conversation history
        assistant_message = response.choices[0].message.content.strip()
        conversation_history.append(
            {"role": "assistant", "content": assistant_message})

        return {"message": "Data loaded successfully and ready for queries",
                "assistant_response": assistant_message}

    except Exception as e:
        return {"error": f"Error sending data: {str(e)}"}

    finally:
        conn.close()
        print("Database connection closed")


@app.post("/api/query_database")
async def query_database(request: QueryRequest):
    global conversation_history

    if len(conversation_history) <= 1:  # Only the system message is in the history
        return {"error": "You must first load the data with /api/send_data_to_openai"}

    try:
        # Add the user's question to the conversation history
        user_message = f"Pregunta del usuario: {request.prompt}"
        conversation_history.append({"role": "user", "content": user_message})

        # Get the response from OpenAI using the conversation history
        response = client.chat.completions.create(
            model="gpt-4.5-preview",
            messages=conversation_history,
            max_tokens=1000
        )

        # Save the response in the conversation history
        assistant_message = response.choices[0].message.content.strip()
        conversation_history.append(
            {"role": "assistant", "content": assistant_message})

        return {"response": assistant_message}

    except openai.RateLimitError:
        return {"error": "OpenAI API rate limit exceeded. Please try again later."}

    except Exception as e:
        return {"error": f"Error calling OpenAI API: {str(e)}"}


@app.get("/api/clear_conversation")
async def clear_conversation():
    global conversation_history
    # Only keep the system message
    conversation_history = [conversation_history[0]]
    return {"message": "Conversation history cleared"}


@app.get("/")
async def root():
    return {"message": "API is working!"}
