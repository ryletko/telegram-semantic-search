from datetime import datetime
import gc
import json
import re
import os
import uuid
from typing import Any

from dotenv import load_dotenv
import psycopg2
from services.language_models import Model, EmbeddingMode
# Load environment variables    
load_dotenv()

# Database connection parameters
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "telegram_search")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "your_password")


class Import:
    id: str
    chat_name: str
    chat_id: int
    type: str
    model_name: str
    timestamp: datetime

    def __init__(self, id: str, chat_name: str, chat_id: int, type: str, model_name: str):
        self.id = id
        self.chat_name = chat_name
        self.chat_id = chat_id
        self.type = type
        self.model_name = model_name
        self.timestamp = datetime.now()


class TelegramJsonImporter:
    id: int
    text: str
    date: datetime
    from_id: str
    from_name: str
    is_self: bool

    def __init__(self, id: int, text: str, date: datetime, from_id: str, from_name: str, is_self: bool):
        self.id = id
        self.text = text
        self.date = date
        self.from_id = from_id
        self.from_name = from_name
        self.is_self = is_self


class MessageChunk:
    id: int
    message_id: int
    import_id: str
    text: str

    def __init__(self, import_id: str, message_id: int, id: int, text: str):
        self.id = id
        self.message_id = message_id
        self.import_id = import_id
        self.text = text

class MessageImporter:
    
    def __load_import_data(self, data: dict[str, str | int], model_name: str) -> Import:
        return Import(str(uuid.uuid4()), str(data["name"]), int(data["id"]), str(data["type"]), model_name)

    def __enumerate_messages(self, import_: Import, data: dict[str, Any]):
        for message in data["messages"]:
            if message["type"] == "message" and isinstance(message.get("text"), str):
                yield TelegramJsonImporter(
                    int(message["id"]),
                    str(message["text"]),
                    datetime.strptime(str(message["date"]), "%Y-%m-%dT%H:%M:%S"),
                    str(message["from_id"]),
                    str(message["from"]),
                    str(message["from_id"]) != "user" + str(import_.chat_id),
                )

    def load_telegram_messages(self, model: Model, file_path: str) -> tuple[Import, int]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            print("Connecting to database...")

            conn = psycopg2.connect(
                host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS
            )

            model_name = model.model_name
            import_ = self.__load_import_data(data, model_name)
            self.__store_import(conn, model_name, import_)

            batch_size = 256
            batch : list[MessageChunk] = []
            processed_count = 0
            for message in self.__enumerate_messages(import_, data):                
                if message.text == "":
                    continue

                self.__store_message(conn, message, import_)

                message_chunks = [MessageChunk(import_.id, message.id, i, chunk.strip()) for i, chunk in enumerate(re.split(r"[.,\n]", message.text)) if chunk.strip()]
                batch.extend(message_chunks)
                
                if len(batch) >= batch_size:
                    self.__store_chunks(conn, model, batch)
                    processed_count += len(batch)
                    batch = []
                    print(f"Processed {processed_count} messages")
            if batch:
                self.__store_chunks(conn, model, batch)
                processed_count += len(batch)

            print(f"Processed {processed_count} messages")
            conn.close()
            return import_, processed_count

        finally:
            del model
            gc.collect()


    def __store_import(self, conn, model_name: str, import_: Import) -> str:
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

    def __store_message(self, conn, message: TelegramJsonImporter, import_: Import):
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (id, import_id, text, date, from_id, from_name, is_self) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (message.id, import_.id, message.text, message.date, message.from_id, message.from_name, message.is_self),
        )
        conn.commit()
        cursor.close()

    def __store_chunks(self, conn, model: Model, chunks: list[MessageChunk]):
        """
        Store the messages in the database.
        """
        cursor = conn.cursor()

        # Create embeddings for the messages
        texts = [chunk.text for chunk in chunks]
        embeddings = model.create_embedding(texts, mode=EmbeddingMode.Document)

        # Insert the messages
        for i, chunk in enumerate(chunks):
            embedding = embeddings[i]
            embedding_json = f"[{','.join(map(str, embedding))}]"
            
            cursor.execute(
                """
                INSERT INTO message_chunks 
                (id, message_id, import_id, text, embedding) 
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    chunk.id,
                    chunk.message_id,
                    chunk.import_id,
                    chunk.text,
                    embedding_json,
                ),
            )

        conn.commit()
        del embeddings
        gc.collect()