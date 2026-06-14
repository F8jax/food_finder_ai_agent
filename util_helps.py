import re
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)

model_name = "nvidia/nemotron-3-nano-4b"

def extract_ingredients(text):
    prompt = f"""
Haal alleen de ingrediënten uit deze tekst.

Regels:
- alleen voedsel/ingrediënten teruggeven
- geen zinnen
- alleen lijst gescheiden door komma

Tekst:
{text}
"""

    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    output = response.choices[0].message.content

    items = [i.strip() for i in output.split(",") if i.strip()]

    return list(dict.fromkeys(items))

def format_ingredients(items):
    items = [i.strip().lower() for i in items if i.strip()]

    if len(items) == 0:
        return ""

    items = [i.capitalize() for i in items]

    if len(items) == 1:
        return items[0]

    if len(items) == 2:
        return f"{items[0]} en {items[1]}"

    return ", ".join(items[:-1]) + f" en {items[-1]}"