import streamlit as st
import time
import re
from openai import OpenAI

# =====================
# LM STUDIO CONNECTIE
# =====================
client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio"
)

model_name = "nvidia/nemotron-3-nano-4b"

# =====================
# HELPERS
# =====================
def smart_split(text):
    text = text.lower()
    text = text.replace(" en ", ",")

    items = re.split(r"[,\n]+", text)

    if len(items) == 1:
        items = text.split()

    return [i.strip() for i in items if i.strip()]


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


# =====================
# API CALL
# =====================
def generate_recipes(items, available_time, cooking_level, diet_prefs):
    formatted_items = format_ingredients(items)
    diet_text = ", ".join(diet_prefs)

    prompt = f"""
Je bent een professionele chef en recept-curator.

Geef EXACT 4 recepten op basis van:

Ingrediënten: {formatted_items}
Beschikbare tijd: {available_time} minuten
Kookniveau: {cooking_level}
Dieetwensen: {diet_text}

BELANGRIJK:
- bedenk meerdere recepten
- kies daarna alleen de 4 BESTE
- kies op basis van smaak, haalbaarheid en creativiteit
- alle recepten moeten binnen tijd en dieet passen

KOOKNIVEAU:
- Beginnend: simpel en weinig stappen
- Gemiddeld: normale recepten
- Thuiskok: iets complexer
- Expert: geavanceerde technieken

OUTPUT FORMAT:
gerecht nr|gerecht|ingredienten|duur|nieuwe ingredienten|

REGELS:
- EXACT 4 regels output
- bereidingstijd <= {available_time} minuten
"""
    start_time = time.time()

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    end_time = time.time()

    answer = response.choices[0].message.content
    model_used = getattr(response, "model", model_name)

    return answer, model_used, end_time - start_time


# =====================
# UI
# =====================
st.title("🍽️ AI Recept Generator (LM Studio)")
st.write("Top 4 beste AI recepten op basis van jouw input")

# =====================
# SESSION STATE
# =====================
if "ingredients" not in st.session_state:
    st.session_state.ingredients = []

# =====================
# INGREDIENT INPUT
# =====================
st.subheader("🥕 Ingrediënten")

new_item = st.text_input("Voeg ingrediënten toe")

col1, col2 = st.columns(2)

with col1:
    if st.button("➕ Toevoegen"):
        if new_item:
            parsed = smart_split(new_item)

            for item in parsed:
                st.session_state.ingredients.append(item)

            st.session_state.ingredients = list(dict.fromkeys(st.session_state.ingredients))

            st.success("Ingrediënten toegevoegd!")

with col2:
    if st.button("🗑️ Reset"):
        st.session_state.ingredients = []
        st.info("Ingrediënten gewist")

# =====================
# TIJD
# =====================
st.subheader("⏱️ Beschikbare tijd")

available_time = st.slider(
    "Kooktijd (minuten)",
    min_value=5,
    max_value=120,
    step=5,
    value=30
)

# =====================
# KOOKNIVEAU
# =====================
st.subheader("👨‍🍳 Kookniveau")

cooking_level = st.selectbox(
    "Kies niveau",
    ["Beginnend", "Gemiddeld", "Thuiskok", "Expert"]
)

# =====================
# DIEETWENSEN
# =====================
st.subheader("🥗 Dieetwensen / voorkeuren")

diet_options = [
    "Geen voorkeur",
    "Vegetarisch",
    "Vegan",
    "Halal",
    "Lactosevrij",
    "Glutenvrij",
    "Low carb",
    "Keto",
    "Geen vis",
    "Geen varkensvlees",
    "Pittig eten vermijden"
]

diet_prefs = st.multiselect(
    "Kies je voorkeuren",
    diet_options
)

if not diet_prefs:
    diet_prefs = ["Geen voorkeur"]

# =====================
# WEERGAVE
# =====================
st.subheader("📦 Huidige ingrediënten")

if len(st.session_state.ingredients) == 0:
    st.info("Nog geen ingrediënten toegevoegd")
else:
    for item in st.session_state.ingredients:
        st.write(f"- {item}")

    st.markdown("### 🗣️ Geformatteerd")
    st.write(format_ingredients(st.session_state.ingredients))

# =====================
# GENERATE
# =====================
if st.button("🍝 Genereer recepten"):

    if len(st.session_state.ingredients) == 0:
        st.warning("Voeg eerst ingrediënten toe!")
    else:
        with st.spinner("AI kiest de 4 beste recepten... 🍳"):
            try:
                answer, model_used, duration = generate_recipes(
                    st.session_state.ingredients,
                    available_time,
                    cooking_level,
                    diet_prefs
                )

                st.success("Top 4 gegenereerd!")

                st.subheader("🍽️ Top 4 beste recepten")
                for line in answer.splitlines():
                    st.write(line)

                st.subheader("📊 Metadata")
                st.write(f"Model: {model_used}")
                st.write(f"Tijd AI: {duration:.2f} sec")
                st.write(f"Tijdslimiet: {available_time} min")
                st.write(f"Niveau: {cooking_level}")
                st.write(f"Dieet: {', '.join(diet_prefs)}")
                st.write(f"Ingrediënten: {format_ingredients(st.session_state.ingredients)}")

                # =====================
                # LINKS
                # =====================
                st.subheader("🔗 Extra links")

                for line in answer.splitlines():
                    match = re.search(r"nieuw ingredient\s*=\s*\((.*?)\)", line)

                    if match:
                        ingredient = match.group(1)
                        url = f"https://www.google.com/search?q=supermarkt+{ingredient}"
                        st.markdown(f"- {ingredient} → [zoeken]({url})")

            except Exception as e:
                st.error(f"Fout bij API call: {e}")