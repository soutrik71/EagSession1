import numpy as np
import ollama

# Example sentence to embed
sentence = "How does AlphaFold work?"

# Get embedding from Ollama using the Python client
op = ollama.embed(
    model="nomic-embed-text:latest",
    input=sentence,
)

# Convert to numpy array
embedding_vector = np.array(op["embeddings"][0], dtype=np.float32)

print(
    f"🔢 Vector length: {len(embedding_vector)}"
)  # Should be 768 for nomic-embed-text
print(f"📈 First 5 values: {embedding_vector[:5]}")
