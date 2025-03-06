import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModel, PreTrainedTokenizer, PreTrainedTokenizerFast # type: ignore
from enum import Enum
from abc import ABC, abstractmethod
import numpy as np
from numpy.typing import NDArray
from torch.nn import functional as F
AVAILABLE_MODELS = {
    'ai-forever/ru-en-RoSBERTa': 'AI-Forever Russian-English model with prefixes',
    'Tochka-AI/ruRoPEBert-e5-base-512': 'Tochka-AI Russian language model (small)',
    'sberbank-ai/sbert_large_nlu_ru': 'Sberbank Russian language model (large)',
    'paraphrase-multilingual-MiniLM-L12-v2': 'Multilingual model (smaller, supports 50+ languages)'
}

# Default model to use if none specified
DEFAULT_MODEL = 'ai-forever/ru-en-RoSBERTa' 

class EmbeddingMode(Enum):
    Document = 'document'
    Query = 'query'

class ModelType(Enum):
    BERT = 'bert'
    SBERT = 'sbert'
    
    @staticmethod
    def get_model_type(model_name: str):
        """
        Determine if the model is a BERT or SBERT type based on its name.
        
        Args:
            model_name (str): The name of the model
            
        Returns:
            ModelType: ModelType.BERT or ModelType.SBERT depending on the model type
        """
        model_name = model_name.lower()
        
        if 'sbert' in model_name or 'sentence' in model_name or 'paraphrase' in model_name:
            return ModelType.SBERT
        else:
            return ModelType.BERT

class Model(ABC):

    model_name: str

    @abstractmethod
    def create_embedding(self, texts: list[str], mode: EmbeddingMode | None = None) -> list[list[float]]:
        pass

class ruEnRoSBERTaModel(Model):
    model: SentenceTransformer
    device: str
    
    MODEL_NAME = 'ai-forever/ru-en-RoSBERTa'

    def __init__(self, model: SentenceTransformer, device: str):
        super().__init__()
        self.model = model
        self.model_name = self.MODEL_NAME

    def create_embedding(self, texts: list[str], mode: EmbeddingMode | None = None) -> list[list[float]]:
        if mode == EmbeddingMode.Document:
            texts = [f"search_document: {text}" for text in texts]
        elif mode == EmbeddingMode.Query:
            texts = [f"search_query: {text}" for text in texts]

        batch_embeddings: NDArray[np.float32] = self.model.encode(texts, convert_to_numpy=True)
        return batch_embeddings.tolist()

    @staticmethod
    def create(device: str) -> Model:
        model = SentenceTransformer(ruEnRoSBERTaModel.MODEL_NAME)
        model = model.to(device)
        return ruEnRoSBERTaModel(model, device)

class SBertModel(Model):
    model: SentenceTransformer
    device: str

    def __init__(self, model: SentenceTransformer, model_name: str, device: str):
        super().__init__()
        self.model = model
        self.model_name = model_name
        self.device = device

    def create_embedding(self, texts: list[str], mode: EmbeddingMode | None = None) -> list[list[float]]:
        batch_embeddings: NDArray[np.float32] = self.model.encode(texts, convert_to_numpy=True)
        return batch_embeddings.tolist()
    
    @staticmethod
    def create(model_name: str, device: str) -> Model: 
        # Load the specified model
        print(f"Loading model: {model_name}")
        model = SentenceTransformer(model_name)
        model = model.to(device)

        return SBertModel(model, model_name, device)

class BertModel(Model):
    model: AutoModel
    tokenizer: PreTrainedTokenizer | PreTrainedTokenizerFast
    device: str

    def __init__(self, model: AutoModel, tokenizer: PreTrainedTokenizer | PreTrainedTokenizerFast, model_name: str, device: str):
        super().__init__()
        self.model = model
        self.model_name = model_name
        self.device = device
        self.tokenizer = tokenizer
    
    def create_embedding(self, texts: list[str], mode: EmbeddingMode | None = None) -> list[list[float]]: 
        """
        Create embeddings for the given texts using the BERT model.
        """

        test_batch = self.tokenizer(texts, return_tensors="pt", padding=True, truncation=True, max_length=512)
        test_batch = {k: v.to(self.device) for k, v in test_batch.items()}
        
        with torch.no_grad():
            outputs = self.model(**test_batch) # type: ignore
            embeddings = outputs.last_hidden_state  # (batch_size, seq_length, hidden_dim)
        
        attention_mask = test_batch["attention_mask"].unsqueeze(-1)
        embeddings = (embeddings * attention_mask).sum(dim=1) / attention_mask.sum(dim=1)
        # embeddings = F.normalize(embeddings, p=2, dim=1)  # L2-нормализация
        
        return embeddings.cpu().numpy().tolist()

    @staticmethod
    def create(model_name: str, device: str) -> Model:
        # Определяем, есть ли GPU

        print(f"Loading model: {model_name}")

        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name, trust_remote_code=True, attn_implementation='sdpa')
        
        # This line moves the model to the specified device (GPU or CPU)
        # It ensures the model uses the appropriate hardware for computation
        model.to(device)

        return BertModel(model, tokenizer, model_name, device)
    
class ModelLoader:	
    
    @staticmethod
    def load_model(model_name: str | None = None) -> Model:
        """Load the specified model or get it from the database"""
        # If no model specified, try to get from database
        
        gpu_available = torch.cuda.is_available()
        device = "cuda" if gpu_available else "cpu"
        if device == "cuda":
            print(f"GPU detected: {torch.cuda.get_device_name(0)}")
            print("Using GPU for embeddings generation")
        else:
            print("No GPU detected. Using CPU for embeddings (this will be slower)")

        if model_name is None:
            model_name = DEFAULT_MODEL

        if (model_name == ruEnRoSBERTaModel.MODEL_NAME):
            return ruEnRoSBERTaModel.create(device)

        model_type = ModelType.get_model_type(model_name)
        if model_type == ModelType.BERT:
            return BertModel.create(model_name, device)
        elif model_type == ModelType.SBERT:
            return SBertModel.create(model_name, device)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")