CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS imports (
	id uuid NOT NULL CONSTRAINT imports_pk PRIMARY KEY,
	timestamp timestamp WITH time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
	chat_name varchar(1000) NOT NULL,
	chat_id varchar(255) NOT NULL,
	type varchar(255) NOT NULL,
	model_name varchar(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
	id int NOT NULL,
	import_id uuid NOT NULL,
	text TEXT NOT NULL,
	date timestamp WITH time zone DEFAULT CURRENT_TIMESTAMP,
	is_self BOOLEAN DEFAULT FALSE,
	embedding vector(1024),
	from_id VARCHAR(255) NOT NULL,
	from_name VARCHAR(255) NOT NULL,
	CONSTRAINT messages_pk PRIMARY KEY (id, import_id),
	CONSTRAINT messages_imports_fk FOREIGN KEY (import_id) REFERENCES imports(id)
);

-- CREATE INDEX IF NOT EXISTS embedding_index ON messages USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS embedding_index ON messages USING hnsw (embedding vector_cosine_ops) WITH (m = 32, ef_construction = 128);
CREATE INDEX IF NOT EXISTS import_id_index ON messages (import_id);