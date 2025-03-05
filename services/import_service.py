import json
import os
import time
import uuid
import torch
import numpy as np
import psycopg2
import argparse
from psycopg2.extras import Json
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from models import DEFAULT_MODEL, AVAILABLE_MODELS
from datetime import datetime
from services.model_service import load_model
import gc

# Load environment variables
load_dotenv()

# Database connection parameters
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "telegram_search")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "your_password")

def create_embedding(texts, model, model_name):
    """
    Create embeddings for a list of texts using batching for efficiency.
    Returns a list of numpy arrays.
    """
    # Add prefix for models that require it
    if model_name == "ai-forever/ru-en-RoSBERTa":
        texts = [f"search_document: {text}" for text in texts]

    # Process texts in batches for better GPU utilization
    all_embeddings = []
    batch_embeddings = model.encode(texts, convert_to_numpy=True)
    all_embeddings.extend(batch_embeddings)
    return all_embeddings


class Import:
    id: str
    chat_name: str
    chat_id: str
    type: str
    model_name: str
    timestamp: datetime

    def __init__(self, id, chat_name, chat_id, type, model_name):
        self.id = id
        self.chat_name = chat_name
        self.chat_id = chat_id
        self.type = type
        self.model_name = model_name
        self.timestamp = datetime.now()


class Message:
    def __init__(self, id, text, date, from_id, from_name, is_self):
        self.id = id
        self.text = text
        self.date = date
        self.from_id = from_id
        self.from_name = from_name
        self.is_self = is_self


def load_import_data(data, model_name) -> Import:
    return Import(str(uuid.uuid4()), data["name"], data["id"], data["type"], model_name)


def enumerate_messages(import_, data):
    for message in data["messages"]:
        if message["type"] == "message" and isinstance(message.get("text"), str):
            yield Message(
                message["id"],
                message["text"],
                message["date"],
                message["from_id"],
                message["from"],
                message["from_id"] != "user" + str(import_.chat_id),
            )


def load_telegram_messages(model, model_name, file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        print("Connecting to database...")

        conn = psycopg2.connect(
            host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS
        )

        import_ = load_import_data(data, model_name)
        store_import(conn, model_name, import_)

        batch_size = 256
        batch = []
        processed_count = 0
        for message in enumerate_messages(import_, data):
            if message.text == "":
                continue
            batch.append(message)
            if len(batch) == batch_size:
                store_in_db(conn, import_, batch, model, model_name)
                processed_count += len(batch)
                batch = []
                print(f"Processed {processed_count} messages")
        if batch:
            store_in_db(conn, import_, batch, model, model_name)
            processed_count += len(batch)

        print(f"Processed {processed_count} messages")
        conn.close()
        return import_, processed_count

    finally:
        del model
        gc.collect()

def store_import(conn, model_name, import_):
    """
    Store the import data in the database.
    """
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO imports (id, chat_name, chat_id, type, model_name) VALUES (%s, %s, %s, %s, %s) RETURNING id",
        (import_.id, import_.chat_name, import_.chat_id, import_.type, model_name),
    )

    conn.commit()
    cursor.close()
    return import_.id


def store_in_db(conn, import_: Import, messages: list[Message], model, model_name: str):
    """
    Store the messages in the database.
    """
    cursor = conn.cursor()

    # Create embeddings for the messages
    texts = [message.text for message in messages]
    embeddings = create_embedding(texts, model, model_name)

    # Insert the messages
    for i, message in enumerate(messages):
        embedding = embeddings[i]
        embedding_json = json.dumps(embedding.tolist())

        cursor.execute(
            """
            INSERT INTO messages 
            (id, import_id, text, date, from_id, from_name, embedding, is_self) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                message.id,
                import_.id,
                message.text,
                message.date,
                message.from_id,
                message.from_name,
                embedding_json,
                message.is_self,
            ),
        )

    conn.commit()
