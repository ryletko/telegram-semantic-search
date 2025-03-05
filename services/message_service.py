"""
Message service for managing messages and search functionality.
"""
from db.database_manager import DatabaseManager

def get_messages_by_import_id(import_id: str, message_id: int, limit: int = 100, offset: int = 0):
	"""
	Get messages for a specific import.
	
	Args:
		import_id (str): The import ID
		limit (int): Number of messages to return
		offset (int): Offset for pagination
		message_id (int): Message ID to start from
	Returns:
		list: Messages from the specified import
	"""
	
	message_id_with_offset = message_id + offset
	
	query = """
		SELECT id, text, date, is_self, import_id, from_id, from_name
		FROM messages 
		WHERE import_id = %s and id >= %s
		ORDER BY date 
		LIMIT %s 
	"""
	results = DatabaseManager.execute_query(query, (import_id, message_id_with_offset, limit), fetch='all')
	
	if not results:
		return []
		
	messages = []
	for row in results:
		messages.append({
			'id': row[0],
			'text': row[1],
			'date': row[2].isoformat() if row[2] else None,
			'is_self': row[3],
			'import_id': import_id,
			'from_id': row[5],
			'from_name': row[6]
		})
		
	return messages

def get_import_by_id(import_id):
	print("get_import_by_id", import_id)
	query = """
		SELECT id, timestamp, chat_name, chat_id, type, model_name
		FROM imports
		WHERE id = %s
	"""
	result = DatabaseManager.execute_query(query, (import_id,), fetch='one')
	
	if result:
		return {
			'id': result[0],
			'timestamp': result[1],
			'chat_name': result[2],
			'chat_id': result[3],
			'type': result[4],
			'model_name': result[5]
		}
	return None

def _get_model_by_import_id(import_id):
	"""
	Load and return the specified embedding model.
	
	Args:
		import_id (str): The import ID
		
	Returns:
		model: The loaded model
	"""
	# If no model specified, use default
	import_ = get_import_by_id(import_id)
	if not import_:
		print(f"Import with ID {import_id} not found")
		return None
		
	model_name = import_["model_name"]
							
	return model_name