# Telegram Semantic Search

A powerful tool for semantically searching through your Telegram chat history using natural language processing and vector embeddings.

## Overview

Telegram Semantic Search allows you to import your Telegram chat export files and perform semantic (meaning-based) searches through your message history. Unlike traditional keyword search, semantic search understands the meaning behind your query and returns messages that are conceptually similar, even if they don't contain the exact keywords.

### Key Features

- Import Telegram chat export files (JSON format)
- Generate vector embeddings for all messages using transformer models
- Perform semantic searches with adjustable similarity thresholds
- View conversation context around search results
- Filter results by specific contacts
- Modern web interface with responsive design

## How It Works

1. The application uses transformer models (like BERT variants) to convert messages into high-dimensional vector embeddings
2. These embeddings capture the semantic meaning of each message
3. When you search, your query is converted to a vector using the same model
4. PostgreSQL with pgvector extension finds messages with similar vectors using cosine similarity
5. Results are ranked by similarity and displayed in the web interface

## Requirements

- Python 3.8+ 
- Node.js 14+ and npm
- PostgreSQL 12+ with pgvector extension
- GPU support is optional but recommended for faster processing

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/telegram_semantic_search.git
cd telegram_semantic_search
```

### 2. Set up a Python virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python -m venv venv
source venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Install PostgreSQL and pgvector

#### For Windows:

Ensure [C++ support in Visual Studio](https://learn.microsoft.com/en-us/cpp/build/building-on-the-command-line?view=msvc-170#download-and-install-the-tools) is installed, and run:

```cmd
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
```

Note: The exact path will vary depending on your Visual Studio version and edition

Then use `nmake` to build:

```cmd
set "PGROOT=C:\Program Files\PostgreSQL\16"
cd %TEMP%
git clone --branch v0.8.0 https://github.com/pgvector/pgvector.git
cd pgvector
nmake /F Makefile.win
nmake /F Makefile.win install
```

See the [installation notes](#installation-notes---windows) if you run into issues

You can also install it with [Docker](#docker) or [conda-forge](#conda-forge).


#### For Linux:

```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Install pgvector from source
git clone --branch v0.8.0 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install

# Enable the extension
sudo -u postgres psql -c "CREATE EXTENSION vector;"
```

#### For macOS:

```bash
# Using Homebrew
brew install postgresql

# Install pgvector
brew install pgvector

# Start PostgreSQL service
brew services start postgresql

# Enable the extension
psql postgres -c "CREATE EXTENSION vector;"
```

### 5. Create a PostgreSQL database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE telegram_search;

\q
```

### 6. Configure environment variables

Copy the example environment file and update it with your settings:

```bash
cp .env.example .env
```

Edit the `.env` file with your database credentials and other settings:

```
# Database configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=telegram_search
DB_USER=postgres
DB_PASSWORD=your_password

# Flask configuration
FLASK_ENV=development
FLASK_DEBUG=1

# Application settings
UPLOAD_FOLDER=uploads
DEFAULT_MODEL=ai-forever/ru-en-RoSBERTa
```

## Running the Application

The application consists of a Flask backend and a Vue.js frontend. You can start both simultaneously using the provided start script:

```bash
# Activate virtual environment if not already activated
# Windows: venv\Scripts\activate
# Linux/macOS: source venv/bin/activate

# Start the application
python start.py
```

This will:
1. Start the Flask backend server on port 5000
2. Start the Vue.js development server on port 5173
3. Open your default web browser to the application

Alternatively, you can start the components separately:

```bash
# Start backend
python app.py

# In a separate terminal, start frontend
cd frontend
npm install  # Only needed first time
npm run dev
```

## How to Use

### 1. Export your Telegram chat history

1. Open Telegram Desktop
2. Go to Settings > Advanced > Export Telegram data
3. Select "JSON" as the format and choose which chats to export
4. Download the export file

### 2. Import the chat export

1. Open the Telegram Semantic Search application in your browser
2. Click "Import Chat"
3. Select your Telegram export JSON file
4. Wait for the import to complete (this may take some time for large chats)

### 3. Search your messages

1. Enter a search query in the search box
2. Adjust similarity threshold if needed (lower values return more results)
3. View results ranked by semantic similarity
4. Click on a result to see the conversation context

## Technical Details

### Architecture

- **Backend**: Flask (Python) with SQLAlchemy
- **Frontend**: Vue.js with Tailwind CSS
- **Database**: PostgreSQL with pgvector extension
- **Embedding Models**: Sentence Transformers (BERT variants)

### Database Schema

The application uses two main tables:

1. **imports**: Stores metadata about imported chat exports
   - id (UUID): Primary key
   - timestamp: Import time
   - chat_name: Name of the chat
   - chat_id: Telegram chat ID
   - type: Type of chat (private, group, etc.)
   - model_name: Embedding model used

2. **messages**: Stores individual messages with embeddings
   - id: Message ID
   - import_id: Foreign key to imports table
   - text: Message content
   - date: Message timestamp
   - is_self: Whether the message is from the user
   - embedding: Vector representation (1024 dimensions)
   - from_id: Sender ID
   - from_name: Sender name

### Vector Search

The application uses pgvector's cosine similarity operator (`<=>`) to find semantically similar messages. The SQL query looks like:

```sql
SELECT 
    m.id, 
    m.text, 
    m.date, 
    m.from_id, 
    m.from_name,
    1 - (m.embedding <=> query_vector) as similarity,
    m.is_self
FROM 
    messages m
WHERE 
    m.import_id = import_id
    AND 1 - (m.embedding <=> query_vector) > min_similarity
ORDER BY 
    similarity DESC
```

## Troubleshooting

### Common Issues

1. **Database connection errors**:
   - Verify PostgreSQL is running
   - Check your database credentials in the `.env` file
   - Ensure pgvector extension is installed

2. **Import failures**:
   - Verify your Telegram export is in JSON format
   - Check that the file is not corrupted
   - Ensure you have sufficient disk space

3. **Slow performance**:
   - Consider using a GPU for faster embedding generation
   - Adjust the batch size in the import service
   - Optimize PostgreSQL settings for your hardware

## License

[MIT License](LICENSE)

## Acknowledgements

- [Sentence Transformers](https://www.sbert.net/) for embedding models
- [pgvector](https://github.com/pgvector/pgvector) for vector similarity search in PostgreSQL
- [Flask](https://flask.palletsprojects.com/) and [Vue.js](https://vuejs.org/) for the web framework 