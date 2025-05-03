from ollama import chat
from ollama import ChatResponse
from ollama import Client
import asyncio
from ollama import AsyncClient

"""
Prerequisites:
- Install the ollama package using pip:
pip install ollama
- Make sure you have the Ollama CLI installed and running.
- Make sure you have the model you want to use downloaded. You can do this by running:
ollama pull <model_name>

Tips:
- You can find a list of available models at https://ollama.com/models.
- You can also use the `ollama list` command to see a list of all models you have downloaded.
- chat function is a wrapper around the Ollama CLI chat command to interact with models.
- we are using the chat function to get a response from a model.
- The chat function takes a model name and a list of messages as input.
- The messages are a list of dictionaries, where each dictionary has a role (user or assistant) and content (the message text).
"""

# This is a simple example of using the chat function to get a response from a model.
- The chat function takes a model name and a list of messages as input.
response: ChatResponse = chat(
    model="smollm2:135m",
    messages=[
        {
            "role": "user",
            "content": "Why is the sky blue?",
        },
    ],
)
print("Response:")
print(response["message"]["content"])
# or access fields directly from the response object
print(response.message.content)

# This is a simple example of using the chat function to get a response from a model with streaming.
stream = chat(
    model="smollm2:135m",
    messages=[{"role": "user", "content": "Why is the sky blue?"}],
    stream=True,
)
print("\n\n")
print("Streaming response:")
for chunk in stream:
    print(chunk["message"]["content"], end="", flush=True)


client = Client(host="http://localhost:11434", headers={"x-some-header": "some-value"})
response = client.chat(
    model="smollm2:135m",
    messages=[
        {
            "role": "user",
            "content": "Why is the sky blue?",
        },
    ],
)
print("\n\n")
print("Custom Client Response:")
print(response["message"]["content"])

# asynchronous example


async def chat():
    message = {"role": "user", "content": "Why is the sky blue?"}
    response = await AsyncClient().chat(model="smollm2:135m", messages=[message])


print("\n\n")
print("Async Client Response:")
resonse = asyncio.run(chat())
print(resonse["message"]["content"])
