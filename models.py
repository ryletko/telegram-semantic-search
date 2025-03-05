"""
Model configuration settings.
"""

# Available models with their descriptions
AVAILABLE_MODELS = {
    'sberbank-ai/sbert_large_nlu_ru': 'Sberbank Russian language model (large)',
    'ai-forever/ru-en-RoSBERTa': 'AI-Forever Russian-English model with prefixes',
    'paraphrase-multilingual-MiniLM-L12-v2': 'Multilingual model (smaller, supports 50+ languages)'
}

# Default model to use if none specified
DEFAULT_MODEL = 'ai-forever/ru-en-RoSBERTa' 