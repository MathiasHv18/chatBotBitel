import shutil
from uuid import uuid4
import asyncio
from fastapi.responses import StreamingResponse
import json
from fastapi import FastAPI
from PyPDF2 import PdfReader
from fastapi.staticfiles import StaticFiles
import base64
import re
from fastapi import Form, File, UploadFile
from collections import defaultdict
import cx_Oracle
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import openai
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
import httpx


app = FastAPI()
# Access folder images with url
app.mount("/images", StaticFiles(directory="images"), name="images")
app.mount("/files", StaticFiles(directory="files"), name="files")



# Client to communicate with CHATGPT
clientGPT = openai.OpenAI(
    api_key=""
)
# Client to communicate with Deepseek
clientDeepSeek = openai.OpenAI(
    api_key="", base_url="https://api.deepseek.com")


lastID = -1
conversations = {}
CODE_EXTENSIONS = {
    "py", "js", "jsx", "ts", "tsx", "java", "kt", "kts", "go", "rb", "php", "cs",
    "cpp", "cxx", "cc", "c", "h", "hpp", "hh", "rs", "swift", "scala", "pl", "pm",
    "sh", "bash", "zsh", "bat", "cmd",
    "html", "htm", "css", "scss", "sass", "less", "vue", "xml",
    "json", "yaml", "yml", "toml", "ini", "env",
    "md", "rst", "org", "adoc", "asciidoc",
    "lua", "dart", "r", "jl", "m", "matlab", "groovy", "clj", "cljs", "lisp", "el", "ex", "exs", "coffee", "jinja", "sql", "ps1",
    "gradle", "makefile", "mk", "cmake", "Dockerfile", "gitignore", "gitattributes", "gitmodules",
    "ejs", "hbs", "mustache", "pug", "twig",

    "vb", "vbs", "asm", "s", "ada", "fs", "fsi", "fsx", "fsscript", "erl", "hrl", "pro", "pas", "d", "nim", "ml", "mli"
}


class Interaction:
    def __init__(self, role, content):
        self.role = role
        self.content = content

    def __repr__(self):
        return f"Interaction(role='{self.role}', content='{self.content}')"


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Windows Mathias
# cx_Oracle.init_oracle_client(lib_dir=r"C:\oracle\instantclient_23_7")

# Linux Mathias
# cx_Oracle.init_oracle_client(  lib_dir="/home/mathias/oracle/instantclient_19_26/")

# Linux Server
cx_Oracle.init_oracle_client(lib_dir=r"/opt/oracle/instantclient_19_26")


DB_CONFIG = {
    "username": "ninhdt4",
    "password": "Bitel@123$",
    "host": "10.121.30.150",  # local
    # "host": "10.121.30.152", #prod
    "port": int("1521"),
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
    cursor.execute(
        "SELECT table_name FROM user_tables")
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


def read_conversation_txt(username):
    conversations_dir = "conversations"
    filename = os.path.join(conversations_dir, f"conversations-{username}.txt")

    conversations[username] = []

    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
            current_role = None
            current_content = []
            valid_roles = {"user", "system", "assistant"}

            for line in lines:
                line = line.strip()

                # Si es una línea vacía, continúa agregando contenido al mensaje actual
                if not line:
                    if current_role and current_content:
                        current_content.append("")
                    continue

                if line.startswith("INITMESSAGE - "):
                    # Si hay un mensaje previo en construcción, agrégalo antes de procesar el nuevo
                    if current_role and current_content:
                        conversations[username].append(Interaction(
                            role=current_role,
                            content="\n".join(current_content),
                        ))

                    # Reiniciar variables para el nuevo mensaje
                    current_content = []
                    current_role = None

                    # Extraer la parte después de "INITMESSAGE - "
                    line = line[len("INITMESSAGE - "):].strip()
                    parts = line.split(" - ", 3)

                    if len(parts) >= 3:
                        datetime_str, model_user, message = parts[:3]
                        message_parts = message.split(": ", 1)

                        if len(message_parts) == 2:
                            role, content = message_parts
                            role = role.strip().lower()
                            content = content.strip()

                            if role in valid_roles:
                                current_role = role
                                current_content.append(content)
                else:
                    # Si la línea no empieza con "INITMESSAGE - ", la agregamos al mensaje actual
                    if current_role:
                        current_content.append(line)

            # Agregar el último mensaje acumulado si hay contenido pendiente
            if current_role and current_content:
                conversations[username].append(Interaction(
                    role=current_role,
                    content="\n".join(current_content),
                ))

    except FileNotFoundError:
        print(f"No conversation history found for user: {username}")
        return False
    except Exception as e:
        print(f"Error reading conversation history for {username}: {str(e)}")

    return conversations[username]


def save_conversation_txt(username, modelUser):
    conversations_dir = "conversations"
    filename = os.path.join(conversations_dir, f"conversations-{username}.txt")

    try:
        with open(filename, "w", encoding="utf-8") as f:
            for message in conversations[username]:
                f.write(
                    f"INITMESSAGE - {datetime.now()} - {modelUser} - {message.role}: {message.content}\n"
                )
        print(f"Saved conversation for user: {username}")
    except Exception as e:
        print(f"Error saving conversation for {username}: {str(e)}")


@app.post("/api/clear_conversation")
async def clear_conversation(request: dict):
    try:
        username = request.get("username")

        conversations_dir = "conversations"
        archivo_conversacion = os.path.join(
            conversations_dir, f"conversations-{username}.txt")

        if os.path.exists(archivo_conversacion):
            os.remove(archivo_conversacion)
            return {"message": "Conversation history cleared"}
        else:
            return {"error": f"No conversation history found for {username}"}
    except Exception as e:
        print(f"{e}")


async def send_data_to_ia(modelUser, clientUser, username):
    conn = get_oracle_connection()

    try:
        print("Sending data to OpenAI...")
        tables = get_all_table_names(conn)
        print("Tables:", tables)

        data_message = "Here is the database information for your analysis:\n"
        for table in tables:
            try:
                df = get_table_data(conn, table)
                data_message += f"Table {table}:\n{df.to_string()}\n\n"
                print(f"Data from {table} completed")
            except Exception as e:
                print(f"Error fetching data from {table}: {str(e)}")
        # Append data to conversation history
        conversations[username].append(
            {"role": "user", "content": data_message})
        save_conversation_txt(username, modelUser)

        # Get the response from OpenAI library
        response = clientUser.chat.completions.create(
            model=modelUser,
            messages=conversations[username],
            max_tokens=4000
        )

        # Save the response in the conversation history
        assistant_message = response.choices[0].message.content.strip()
        conversations[username].append(Interaction(
            role="system", content=assistant_message))
        save_conversation_txt(username, modelUser)
        return {"message": "Data loaded successfully and ready for queries",
                "assistant_response": assistant_message}

    except Exception as e:
        return {"error": f"Error sending data: {str(e)}"}

    finally:
        print("Database connection closed")


@app.post("/api/inputModel")
async def initializeChat(request: dict):
    modelUser = request.get("modelUser")
    username = request.get("username")
    isChurn = request.get("isChurn")
    modelToUse, userClient = processInputModel(modelUser)
    await getConversations(username)
    return {"response": "User created"}


@app.get("/api/getUserConversations")
async def getConversations(username: str):
    output = read_conversation_txt(str(username))
    if output == False:
        conversations[username] = [
            Interaction(
                role="system",
                content="""
This GPT acts as a data analyst specialized in churn prediction analysis for telecommunications company customers. It works with multiple datasets related to customer activity, refills, complaints, consumption details, payments, discounts, packages, customer demographics, and product offers.

### Primary Tasks:
1. **Read and Understand Data**: Upon user request, the GPT will read all available datasets and summarize their structure, including column names and data types.
2. **Merge Datasets**: When requested, it will merge all relevant datasets using common identifiers such as ISDN or SUB_ID.
3. **Churn Prediction Analysis**:
   - Identify customer activity patterns.
   - Analyze refill trends, complaints, and discount usage.
   - Evaluate product package engagement.
   - Assess payment behavior.
   - Generate churn risk levels (high, moderate, low) based on historical data.

### How the GPT Responds:
* It summarizes the dataset structure upon request.
* It merges datasets when asked, ensuring compatibility through common keys.
* It provides churn predictions based on historical data trends.
* It avoids discussing technical errors, focusing on user-friendly analysis.

Users can directly request specific dataset insights, merging, or predictive churn analysis."""
            )
        ]
        save_conversation_txt(username, "null")

    return conversations[username]


def processInputModel(modelUser):
    modelToUse = ''
    if modelUser == 2:
        modelToUse = 'gpt-4.1'
        clientUser = clientGPT
    else:
        modelToUse = 'deepseek-chat'
        clientUser = clientDeepSeek

    return modelToUse, clientUser


@app.get("/api/getAllChats")
async def getChats():
    chat_ids = []
    conversations_dir = "conversations"  # Directorio correcto

    if not os.path.exists(conversations_dir):
        # Si la carpeta no existe, devuelve lista vacía
        return {"chat_ids": []}

    for filename in os.listdir(conversations_dir):
        match = re.match(r"conversations-(\d+)\.txt", filename)
        if match:
            chat_ids.append(int(match.group(1)))

    chat_ids.sort()
    return {"chat_ids": chat_ids}


@app.get("/api/lastChat")
async def getChatId():
    global lastID
    try:
        lastID = lastID + 1
        return {"response": lastID}
    except Exception as e:
        return e


@app.post("/api/chatUser")
async def getChatUser(request: dict):
    id = request.get("username")
    conversations[id] = []
    read_conversation_txt(id)

    return {"response": conversations[id]}


def storeImage(nameImg, base64Img):

    try:
        # Get fileType
        firstSplit, secondSplit = base64Img.split("/", 1)
        fileType, rest = secondSplit.split(";", 1)

        # Get only encoded base64
        header, encoded = base64Img.split(",", 1)

        image_data = base64.b64decode(encoded)
        save_path = os.path.join("images", f'{nameImg}')

        with open(save_path, "wb") as f:
            f.write(image_data)

        return fileType
    except Exception as e:
        return {"response": e}


@app.post("/api/query_database")
async def query_database(modelUser: int = Form(...),
                         username: str = Form(...),
                         isChurn: bool = Form(...),
                         prompt: str = Form(...),
                         images: str = Form(...),
                         files: List[UploadFile] = File(default=[])
                         ):
    pdfText = None
    textCode = None
    await getConversations(username)
    conversation = conversations[username]
    modelToUse, userClient = processInputModel(int(modelUser))

    if isChurn:
        await send_data_to_ia(modelToUse, userClient, username)

    filenames = await storeFiles(files)
    if filenames:
        pdfText = await readPdf(files)
        textCode = await readCode(filenames)

    await storeImages(images, conversation)

    conversation.append(
        Interaction(
            role="user",
            content=prompt,
        )
    )

    try:
        openai_messages = []
        if filenames:
            filenames_str = ", ".join(filenames)
            conversation.append(
                Interaction(
                    role="user",
                    content=f"I have uploaded the following files: {filenames_str}"
                )
            )

        if pdfText:
            conversation.append(
                Interaction(
                    role="user",
                    content=f"Here is the extracted content from the PDFs:\n{pdfText}"
                )
            )

        if textCode:
            conversation.append(
                Interaction(
                    role="user",
                    content=f"Here is the extracted content from the code files:\n{textCode}"
                )
            )

        for msg in conversation:
            openai_messages.append({
                "role": msg.role,
                "content": msg.content
            })

        save_conversation_txt(username, modelUser)

        # Bot response
        # assistant_message = await getChurnOutput(
        #    userClient, modelToUse, openai_messages) if isChurn else await getBasicOutput(
        #        userClient, modelToUse, openai_messages)

        async def event_generator():
            assistant_message = ''
            response = userClient.chat.completions.create(
                model=modelToUse,
                messages=openai_messages,
                max_tokens=800,
                stream=True)

            for chunk in response:
                delta = chunk.choices[0].delta
                if delta.content is not None:
                    assistant_message = assistant_message + delta.content
                    yield delta.content
                    await asyncio.sleep(0)

            conversation.append(
                Interaction(
                    role="assistant",
                    content=assistant_message
                )
            )

            save_conversation_txt(username, modelUser)

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except Exception as e:
        return {"error": f"Error calling OpenAI API: {str(e)}"}


@app.post("/api/generateImage")
async def getImageOutput(request: dict):
    promptUser = request.get("prompt")
    image_quality = request.get("image_quality", "standard")
    modelToUse = request.get("modelToUse", "dall-e-3")
    username = request.get("username")
    await getConversations(username)
    conversation = conversations[username]
    conversation.append(
        Interaction(
            role="user",
            content=promptUser,
        )
    )
    save_conversation_txt(username, modelToUse)

    response = clientGPT.images.generate(
        model=modelToUse,
        prompt=promptUser,
        size="1024x1024",
        quality=image_quality,
        n=1,
    )

    image_url = response.data[0].url
    conversation.append(
        Interaction(
            role="assistant",
            content=image_url,
        )
    )
    save_conversation_txt(username, modelToUse)

    return {"response": image_url}


async def getChurnOutput(userClient, modelToUse, openai_messages):
    response = userClient.chat.completions.create(
        model=modelToUse,
        messages=openai_messages,  # conversations[username]
        temperature=0.1,  # Low value = more deterministic
        top_p=0.95,  # High precision
        presence_penalty=0.1,  # Low presence penalty
        frequency_penalty=0.1,  # Avoid repetition
        max_tokens=4096  # may need change
    )
    assistant_message = response.choices[0].message.content.strip()
    return assistant_message


async def getBasicOutput(userClient, modelToUse, openai_messages):
    response = userClient.chat.completions.create(
        model=modelToUse,
        messages=openai_messages,  # conversations[username]
        max_tokens=800  # may need change

    )
    assistant_message = response.choices[0].message.content.strip()
    return assistant_message


async def readPdf(pdfFile: UploadFile):
    text = ''
    try:
        if pdfFile:
            for pdf in pdfFile:
                if pdf.filename.lower().endswith('.pdf'):
                    reader = PdfReader(pdf.file)
                    for page in reader.pages:
                        text += page.extract_text()
            return text
    except Exception as e:
        return {"response": e}

    return None


async def storeFiles(files):
    filenames = []

    if files:
        for file in files:
            filename = f"{uuid4()}_{file.filename}"
            filenames.append(filename)
            save_path = os.path.join("files", f'{filename}')

            with open(save_path, "wb") as f:
                content = await file.read()
                f.write(content)

            file.file.seek(0)
        return filenames
    return False


async def storeImages(images, conversation):
    images = json.loads(images)
    for img in images:
        filename = img["filename"]
        base64_data = img["base64"]

        filetype = storeImage(filename, base64_data)

        img_url = f'http://181.176.39.56/static/{filename}'
        conversation.append(
            Interaction(
                role="user",
                content=[
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": img_url
                        }
                    }
                ]
            )
        )


async def readCode(filenames):
    textCode = ''
    for filename in filenames:
        filepath = os.path.join("files", f'{filename}')
        extension = filename.split(".")[-1].lower()
        if extension in CODE_EXTENSIONS:
            with open(filepath, "r", encoding="utf-8") as f:
                textCode += f.read()
    if textCode == '':
        return None
    return f"```{textCode}\n```"
