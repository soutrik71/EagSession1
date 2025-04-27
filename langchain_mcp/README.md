## UV issue
For client , we use langchain google gemini packages which has some spm specific requirements.
For this we maintain a mininal requirements.txt file.
The commands to run uv using this file are:
```bash
uv pip install -r requirements.min.txt
uv pip sync requirements.min.txt
uv pip compile requirements.min.txt -o requirements.min.lock.txt
```


