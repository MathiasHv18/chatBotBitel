from fastapi import FastAPI
import cx_Oracle
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import openai
import dotenv
import os
dotenv.load_dotenv()
# Usa la variable de entorno correcta
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app = FastAPI()

# Cors allow *
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Server frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.get("/api/table_names")
async def get_table_names_endpoint():
    """ Retorna la lista de tablas disponibles en la BD """
    conn = get_oracle_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT table_name FROM user_tables ORDER BY table_name")
    table_names = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return {"table_names": table_names}


def get_table_data(conn, table_name, limit=30):
    cursor = conn.cursor()

    query = f"SELECT * FROM {table_name} WHERE ROWNUM <= :limit"
    cursor.execute(query, {"limit": limit})

    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    cursor.close()

    return pd.DataFrame(rows, columns=columns)


def get_table_metadata(conn, table_name):
    cursor = conn.cursor()
    query = f"""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM USER_TAB_COLUMNS
        WHERE TABLE_NAME = :table_name
    """
    cursor.execute(query, {"table_name": table_name})
    metadata = {row[0]: row[1] for row in cursor.fetchall()}
    cursor.close()
    return metadata


class QueryRequest(BaseModel):
    table_name: str
    prompt: str


@app.post("/api/query_table")
async def query_table(request: QueryRequest):
    conn = get_oracle_connection()

    try:
        df = get_table_data(conn, request.table_name, limit=5)
        metadata = get_table_metadata(conn, request.table_name)
        conn.close()

        table_summary = (
            f"La tabla '{request.table_name}' contiene las siguientes columnas:\n"
            + "\n".join([f"- {col}: {dtype}" for col,
                        dtype in metadata.items()])
            + f"\n\nAquí hay una muestra:\n{df.to_markdown(index=False)}\n\n"
            + f"Pregunta del usuario: {request.prompt}"
        )

        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un asistente de SQL experto en análisis de bases de datos."},
                {"role": "user", "content": table_summary},
            ],
            max_tokens=200
        )

        return {"response": response.choices[0].message.content.strip()}
    except Exception as e:
        return {"error": str(e)}
