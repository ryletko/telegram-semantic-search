import torch
from sentence_transformers import SentenceTransformer
from config.models import DEFAULT_MODEL

def load_model(model_name=None):
    """Load the specified model or get it from the database"""
    # If no model specified, try to get from database
    if model_name is None:
        model_name = DEFAULT_MODEL

    # Check GPU availability
    gpu_available = torch.cuda.is_available()
    if gpu_available:
        print(f"GPU detected: {torch.cuda.get_device_name(0)}")
        print("Using GPU for embeddings generation")
    else:
        print("No GPU detected. Using CPU for embeddings (this will be slower)")

    # Load the specified model
    print(f"Loading model: {model_name}")
    model = SentenceTransformer(model_name)
    if gpu_available:
        model = model.to("cuda")

    return model, model_name