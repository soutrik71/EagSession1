import numpy as np
import ollama
from scipy.spatial.distance import cosine

# 🎯 Phrases to compare
sentences = [
    "How does AlphaFold work?",
    "How do proteins fold?",
    "What is the capital of France?",
    "Explain how neural networks learn.",
]

# 🧠 Get embeddings using Ollama Python client
embeddings = [
    np.array(
        ollama.embed(model="nomic-embed-text:latest", input=s)["embeddings"][0],
        dtype=np.float32,
    )
    for s in sentences
]


# 🔁 Compare all pairs using cosine similarity
def cosine_similarity(v1, v2):
    return 1 - cosine(v1, v2)  # 1 = perfect match


print("🔍 Semantic Similarity Matrix:\n")
for i in range(len(sentences)):
    for j in range(i + 1, len(sentences)):
        sim = cosine_similarity(embeddings[i], embeddings[j])
        print(f'"{sentences[i]}" ↔ "{sentences[j]}" → similarity = {sim:.3f}')
