"""
Main application file for the Telegram semantic search tool.
"""     
import os
import secrets
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Import services
from services.message_service import get_messages_by_import_id
from services.message_importer import MessageImporter
from services.message_finder import MessageFinder
from db.init_db import initialize_database
from services.language_models import ModelLoader
# Create Flask app

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.secret_key = secrets.token_hex(16)
CORS(app, supports_credentials=True)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
initialize_database()

# Message routes
@app.route("/api/search", methods=["POST"])
def search():
    """Search for messages using semantic similarity."""
    
    data = request.json
    if data is None:
        return jsonify({'error': 'No data provided'}), 400
    
    import_id = data.get("import_id")
    query = data.get('query', '')
    limit = int(data.get('limit', 200))
    min_similarity = float(data.get('min_similarity', 0.3))
    page = int(data.get('page', 1))
    contact_id = data.get('contact_id', None)
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
        
    model = ModelLoader.load_model()    
    
    messages = MessageFinder().search_messages(
        model=model,
        query=query,
        import_id=import_id,
        limit=limit,
        min_similarity=min_similarity,
        page=page,
        contact_id=contact_id
    )
    
    # Format the results to match what the frontend expects
    results = []
    for msg in messages:
        results.append({
            'id': msg['id'],
            'import_id': msg['import_id'],
            'text': msg['text'],
            'date': msg['date'],
            'from_id': msg['from_id'],
            'from_name': msg['from_name'],
            'similarity': msg['similarity'],
            'is_self': msg['is_self'],
        })
    
    return jsonify({'results': results})

@app.route("/api/history", methods=["GET"])
def history():
    """Get message history for a specific chat."""
    import_id = request.args.get("import_id")
    message_id = int(request.args.get("message_id", 0)) 
    limit = int(request.args.get("limit", 100))
    offset = int(request.args.get("offset", 0))

    if not import_id:
        return jsonify({"error": "Import ID is required"}), 400

    messages = get_messages_by_import_id(import_id, message_id, limit, offset)
    return jsonify({"messages": messages})


# Import routes
@app.route("/api/import", methods=["POST"])
def import_messages():
    """Import Telegram messages from a JSON file."""
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files["file"]
    
    # Explicitly check if filename is None before accessing it
    if file.filename is None or file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not file.filename.lower().endswith(".json"):
        return jsonify({"error": "File must be a JSON file"}), 400

    # Save file
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)
    
    # Load the model
    model = ModelLoader.load_model()

    # Load and process messages
    import_, processed_count = MessageImporter().load_telegram_messages(model, file_path)

    # Delete file after import
    try:
        os.remove(file_path)    
    except Exception as e:
        print(f"Error removing file: {e}")

    return jsonify({"import":
        {
            "import_id": import_.id,
            "processed_count": processed_count,
            "chat_id": import_.chat_id,
            "chat_name": import_.chat_name,
            "model_name": import_.model_name,
            "timestamp": import_.timestamp.isoformat()
        }})


if __name__ == "__main__":
    app.run(debug=True)
