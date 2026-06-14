import time
from openai import OpenAI
from util_helps import format_ingredients

client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)

model_name = "nvidia/nemotron-3-nano-4b"


def generate_recipes(items, available_time, cooking_level, diet_prefs):
    formatted_items = format_ingredients(items)
    diet_text = ", ".join(diet_prefs)

    prompt = f"""
Je bent een professionele chef.

Geef EXACT 4 recepten:

Ingrediënten: {formatted_items}
Tijd: {available_time} minuten
Niveau: {cooking_level}
Dieet: {diet_text}

OUTPUT:
gerecht nr|gerecht|ingredienten|duur|nieuwe ingredienten|

- EXACT 4 regels
"""

    start = time.time()

    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    end = time.time()

    return (
        response.choices[0].message.content,
        getattr(response, "model", model_name),
        end - start
    )


def generate_recipe_detail(dish_name, items, available_time, cooking_level, diet_prefs):
    formatted_items = format_ingredients(items)
    diet_text = ", ".join(diet_prefs)

    prompt = f"""
Maak een volledig recept voor:

Gerecht: {dish_name}
Ingrediënten: {formatted_items}
Tijd: {available_time}
Niveau: {cooking_level}
Dieet: {diet_text}

Geef:
- titel
- ingrediënten
- stappen
- tips
"""

    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    return response.choices[0].message.content