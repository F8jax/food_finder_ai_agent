import streamlit as st
from util_helps import extract_ingredients, format_ingredients
from ai_service import generate_recipes, generate_recipe_detail

# STATE
if "page" not in st.session_state:
    st.session_state.page = "home"
    
if "ingredients" not in st.session_state:
    st.session_state.ingredients = []

if "dishes" not in st.session_state:
    st.session_state.dishes = []

if "selected_dish" not in st.session_state:
    st.session_state.selected_dish = None


st.title("🍽️ AI Recept Generator")

# INGREDIENTEN
st.subheader("🥕 Ingrediënten")
new_item = st.text_input("Voeg toe")

if st.button("➕ Toevoegen"):
    if new_item:
        parsed = extract_ingredients(new_item)

        for item in parsed:
            st.session_state.ingredients.append(item)

        st.session_state.ingredients = list(dict.fromkeys(st.session_state.ingredients))

        st.success("Ingrediënten toegevoegd!")

        st.session_state.ingredients = list(dict.fromkeys(st.session_state.ingredients))

if st.button("🗑️ Reset"):
    st.session_state.ingredients = []
    st.session_state.dishes = []

st.subheader("📦 Ingrediënten")

if st.session_state.ingredients:
    st.write(format_ingredients(st.session_state.ingredients))
else:
    st.info("Nog geen ingrediënten")

# SETTINGS
available_time = st.slider("Tijd", 5, 120, 30, 5)

cooking_level = st.selectbox(
    "Niveau",
    ["Beginnend", "Gemiddeld", "Thuiskok", "Expert"]
)

diet_prefs = st.multiselect("Dieet", ["Vegetarisch", "Vegan", "Halal"])

if not diet_prefs:
    diet_prefs = ["Geen voorkeur"]

# GENERATE
if st.button("🍝 Genereer"):

    answer, model, duration = generate_recipes(
        st.session_state.ingredients,
        available_time,
        cooking_level,
        diet_prefs
    )

    st.session_state.dishes = []

    for line in answer.splitlines():
        parts = line.split("|")
        if len(parts) > 1:
            st.session_state.dishes.append(parts[1])
    st.text(answer)

    tab1, tab2 = st.tabs(["🍽️ Recepten", "📖 Recept detail"])

    with tab1:
        st.subheader("🍽️ Top 4 recepten")

        st.text(answer)

        if st.session_state.dishes:
            st.session_state.selected_dish = st.selectbox(
                "Kies gerecht",
                st.session_state.dishes
        )

    with tab2:
        st.subheader("📖 Uitgewerkt recept")

        if st.session_state.selected_dish:

            recipe = generate_recipe_detail(
                st.session_state.selected_dish,
                st.session_state.ingredients,
                available_time,
                cooking_level,
                diet_prefs
            )

            st.write(recipe)