import gc
import json

import torch

from db.database_manager import DatabaseManager
from services.import_service import create_embedding
from services.message_service import _get_model_by_import_id
from services.model_service import load_model
def search_messages(
    query, import_id, limit=20, min_similarity=0.3, page=1, contact_id=None
):
    """
    Search messages using semantic similarity.

    Args:
        query (str): The search query
        model_name (str): Name of the model to use for embedding
        limit (int): Number of results per page
        min_similarity (float): Minimum similarity threshold
        page (int): Page number for pagination
        contact_id (str): Optional contact ID to filter by

    Returns:
        dict: Search results with pagination info
    """

    try:
        # Load the model
        model_name = _get_model_by_import_id(import_id)
        if not model_name:
            return []

        model, _ = load_model(model_name)

        embedding = model.encode(f"search_query: {query}", convert_to_numpy=True)
        query_embedding_json = json.dumps(embedding.tolist())

        # Calculate offset
        offset = (page - 1) * limit

        # Build the query and parameters
        sql_query = """
                SELECT 
                    m.id, 
                    m.text, 
                    m.date, 
                    m.from_id, 
                    m.from_name,
                    1 - (m.embedding <=> %s::vector) as similarity,
                    m.is_self
                FROM 
                    messages m
                WHERE 
                    m.import_id = %s
                    AND 1 - (m.embedding <=> %s::vector) > %s
            """

        # Start with base parameters
        params = [query_embedding_json, import_id, query_embedding_json, min_similarity]

        # Add contact filter if needed
        if contact_id:
            sql_query += " AND m.from_id = %s"
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
                    "id": row[0],
                    "import_id": import_id,
                    "text": row[1],
                    "date": row[2].isoformat() if row[2] else None,
                    "from_id": row[3],
                    "from_name": row[4],
                    "similarity": float(row[5]),
                    "is_self": row[6]
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