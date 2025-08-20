import openai

server_url = "http://localhost:8000/v1"

client = openai.OpenAI(
    base_url=server_url,
    api_key="anyvalue"
)

response = client.chat.completions.create(
    model="anyvalue",
    messages=[
        {"role": "user", "content": "hi, how are you?"}
    ],
    temperature=0.7,
    max_tokens=500
)

assistant_reply = response.choices[0].message.content
print(assistant_reply)
