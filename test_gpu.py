import torch
from sentence_transformers import SentenceTransformer

# Check GPU availability
print(f"GPU available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU count: {torch.cuda.device_count()}")
    print(f"GPU name: {torch.cuda.get_device_name(0)}")
    
# Load model and move to GPU
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
model = model.to('cuda')
print("Model loaded on GPU successfully")

# Test with a simple sentence
test_embedding = model.encode("Это тестовое предложение на русском языке.")
print(f"Embedding shape: {test_embedding.shape}")
print("Embedding generated successfully!")