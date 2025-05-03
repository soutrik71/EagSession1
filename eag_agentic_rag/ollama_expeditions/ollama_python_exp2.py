import ollama
from ollama import Client, AsyncClient


"""
We we use direct api calls to the ollama server, we can use the ollama python client.
we use chat and generate functions to get responses from the model.
"""
# chat
response = ollama.chat(
    model="smollm2:360m",
    messages=[
        {
            "role": "user",
            "content": "Who was Subhas Chandra Bose and what was his role in the Indian independence movement?",
        },
    ],
)

print("Response:")
print(response["message"]["content"])

# generate
response = ollama.generate(
    model="smollm2:360m",
    prompt="Who was Bhagat Singh and what was his role in the Indian independence movement?",
)

print("\n\n")
print("Response:")
print(response["response"])

# list
# print(ollama.list())


### additional commands
"""
# Create
ollama.create(model='example', from_='llama3.2', system="You are Mario from Super Mario Bros.")
# Copy
ollama.copy('llama3.2', 'user/llama3.2')
# Delete
ollama.delete('llama3.2')
# Pull
ollama.pull('llama3.2')
"""

### next we test embedding models
# embed
op = ollama.embed(
    model="nomic-embed-text:latest",
    input="The quick brown fox jumps over the lazy dog",
)
print("\n\n")
print("Embedding:")
print(len(op["embeddings"][0]))

# batch embed
op = ollama.embed(
    model="nomic-embed-text:latest",
    input=[
        "The quick brown fox jumps over the lazy dog",
        "What is the capital of France?",
    ],
)
print("\n\n")
print("Embedding:")
print(len(op["embeddings"]))
print(len(op["embeddings"][0]))
