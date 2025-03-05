// Type definitions for our application

export interface SearchResult {
  id: number;
  import_id: string;
  text: string;
  date: string;
  from_id: string;
  from_name: string;
  similarity?: number; // Optional for search results
  is_self?: boolean; // Whether this message was sent by the user
}

export interface SearchResponse {
  results: SearchResult[];
}

export interface HistoryResponse {
  messages: HistoryMessage[];
}

export interface HistoryMessage {
  id: number;
  text: string;
  date: string;
  is_self: boolean;
  import_id: string;
  from_id: string;
  from_name: string;
}

export interface Import {
  import_id: string;
  chat_name: string;
  chat_id: string;
  processed_count: number;
  model_name: string;
  timestamp: string;
}
