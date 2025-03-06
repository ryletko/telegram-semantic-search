import gc

from db.database_manager import DatabaseManager
from services.language_models import EmbeddingMode

class MessageFinder():
 
    def search_messages(self, model, query, import_id, limit=20, min_similarity=0.3, page=1, contact_id=None):

        try:
            embedding = model.create_embedding([query], mode=EmbeddingMode.Query)
            embedding_json = f"[{','.join(map(str, embedding[0]))}]"

            # Calculate offset
            offset = (page - 1) * limit

            # Check that import and model are compatible
            sql_query = """
                SELECT model_name FROM imports WHERE id = %s
            """
            params = [import_id]
            results = DatabaseManager.execute_query(sql_query, params, fetch="one")
            if results[0] != model.model_name:
                raise ValueError("Import and model are not compatible. Import model is %s", results[0])

            # Build the query and parameters
            sql_query = """
                    SELECT
                        m.import_id,
                        m.message_id,
                        msg.text,
                        msg.date,
                        msg.from_id,
                        msg.from_name,
                        msg.is_self,
                        1 - (m.embedding <=> %s::vector) as similarity
                    FROM message_chunks m
                    JOIN messages msg ON m.message_id = msg.id and msg.import_id = m.import_id
                    WHERE 
                        m.import_id = %s
                        AND 1 - (m.embedding <=> %s::vector) > %s
                """

            # Start with base parameters
            params = [embedding_json, import_id, embedding_json, min_similarity]

            # Add contact filter if needed
            if contact_id:
                sql_query += " AND msg.from_id = %s"
                params.append(contact_id)

            # Add ordering and limit
            sql_query += """
                    ORDER BY 
                        similarity DESC
                    LIMIT %s OFFSET %s
                """
            params.extend([limit, offset])

            print("SQL Query:", sql_query)
            print("Params:", params)

            results = DatabaseManager.execute_query(sql_query, params, fetch="all")

            if not results:
                return []

            messages = []
            for row in results:
                messages.append(
                    {
                        "import_id": row[0],
                        "id": row[1],
                        "text": row[2],
                        "date": row[3].isoformat() if row[3] else None,
                        "from_id": row[4],
                        "from_name": row[5],
                        "is_self": row[6],
                        "similarity": float(row[7]),
                    }
                )

            print(f"Found {len(messages)} results")
                    
            return messages

        except Exception as e:
            print(f"Error during search: {str(e)}")
            import traceback

            traceback.print_exc()
            return []

        finally:
            del embedding
            del model
            gc.collect()