from openai import OpenAI

client = OpenAI()

resp = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[{"role": "user", "content": "Hello from my Poetry project"}],
)

print(resp.choices[0].message.content)
