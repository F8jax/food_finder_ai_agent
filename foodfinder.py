# %% [markdown]
# Imports

# %%
import geocoder
import chromadb
import uuid
import time
import requests
import webbrowser
import sys
from sentence_transformers import SentenceTransformer

# %% [markdown]
# embedding model laden

# %%
embedding_model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# %% [markdown]
# vector Database aanmaken

# %%
client = chromadb.PersistentClient(path="./recept_database")

suggestie_collection = client.get_or_create_collection(
    name="recept_suggesties"
)

recept_collection = client.get_or_create_collection(
    name="volledige_recepten"
)

# %% [markdown]
# gekozen ingredienten invullen

# %%
items = []

print('')

while True:
    item = input("Welke ingredienten zou je willen gebruiken? (type stop om te stoppen): ")

    if item == "stop":
        break

    items.append(item)

# %% [markdown]
# selecteren welke supermarkt je boodschappen doet

# %%
destination = input('Welke supermarkt zou jij naartoe willen gaan?  ( vul supermarkt in of niks)')

# %%
destination = destination.lower()

if  "albert heijn" in destination or "alber" in destination or 'hein' in destination or destination == "ah":
    supermarkt = "https://www.ah.nl/zoeken?query="

elif "plus" in destination:
    supermarkt = "https://www.plus.nl/zoekresultaten?SearchTerm="

elif "jumbo" in destination or "jum" in destination:
    supermarkt = "https://www.jumbo.com/producten/?searchType=keyword&searchTerms="

elif "spar" in destination or 'spa' in destination:
    supermarkt = "https://www.spar.nl/zoek/?fq="

elif "lidl" in destination or "lid" in destination or "lit" in destination or "lil" in destination:
    supermarkt = 'https://www.lidl.nl/q/search?q='

else:
    supermarkt = "https://google.com/search?q=supermarkt+voor+"

# %%
aantal_tijd = input('Hoeveel tijd heeft U (geef antwoord in minuten tussen de 5 en 60)?')

# %%
kookniveau = input('Wat is uw kookniveau? Geeft antwoord in makkelijk, gemiddeld of moeilijk')

# %% [markdown]
# pak public IP voor locatie

# %%
g = geocoder.ip("me")
regio = g.city
lat = g.latlng[0]
lon = g.latlng[1]

# %% [markdown]
# Query voor de vector DB

# %%
def build_query(items):
    return  ', '.join(items)

# %% [markdown]
# Uitzoeken welke rcepten erop lijken

# %%
def get_similar_recipes(items, amount):

    query = build_query(items)
    embedding = embedding_model.encode(query)

    result = suggestie_collection.query(
        query_embeddings=[embedding.tolist()],
        n_results=amount
    )

    if len(result["documents"]) == 0:
        return result

    if len(result["documents"][0]) == 0:
        return result

    return result

# %% [markdown]
# Formatteren voor betere prompting

# %%
def format_similar(results):
    if not results["documents"]:
        return ""

    return "\n".join(results["documents"][0][:5])

# %% [markdown]
# Verglijkbare waardes in een var stoppen

# %%
print(lat)
print(lon)

results = get_similar_recipes(items, len(items))
similar_recipes = format_similar(results)

# %% [markdown]
# De standaard prompt

# %%
prompts = [
    f"""
Genereer EXACT 5 verschillende gerechten op basis van deze ingrediënten:

{items}

Dit is de maximale tijd dat een recept mag duren:

{aantal_tijd}

Recepten moeten op dit kookniveau vallen:

{kookniveau}

Vergelijkbare recepten uit eerdere sessies:

{similar_recipes}

BELANGRIJKE REGELS:
- Geef EXACT 5 regels terug.
- Geen uitleg voor of na de regels.
- Geen markdown.
- Geen opsommingstekens.
- Elke regel moet EXACT dit formaat hebben:

gerecht_nr | gerecht | ingredienten | duur | nieuw ingredient = (ingredient)

VOORBEELD:
1 | Pasta met kip | kip, pasta, ui | 25 min | nieuw ingredient = (parmezaanse kaas)

EXTRA REGELS:
- Gebruik zoveel mogelijk ingrediënten uit de opgegeven lijst.
- Maximaal 1 nieuw ingrediënt per gerecht.
- Bereidingstijd maximaal 30 minuten.
- Het nieuwe ingrediënt MOET tussen haakjes staan.
- De tekst 'nieuw ingredient = ...' moet altijd het laatste onderdeel van de regel zijn.
- Gebruik het pipe-teken '|' uitsluitend als scheidingsteken.
- Gebruik geen pipe-tekens in gerechtnamen of ingrediënten.
- Nummer de gerechten van 1 t/m 5.

Geef alleen de 5 regels terug.
"""
]

# %%
def create_search_text(recipe_text):

    parts = recipe_text.split("|")

    if len(parts) < 3:
        return recipe_text

    gerecht = parts[1].strip()
    ingredienten = parts[2].strip()

    return f"""
gerecht: {gerecht}
ingredienten: {ingredienten}
"""

# %% [markdown]
# Recepten opslaan

# %%
def save_full_recipe(recipe_text, liked=True):

    embedding = embedding_model.encode(recipe_text)

    recept_collection.add(
    ids=[str(uuid.uuid4())],
    documents=[recipe_text],
    embeddings=[embedding.tolist()],
    metadatas=[{
        "ingredients" : ",".join(items),
        "kookniveau" : kookniveau,
        "kooktijd" : int(aantal_tijd),
        "liked": liked
    }]
)

# %%
def save_suggestion(recipe_text, liked=True):

    search_text = create_search_text(recipe_text)
    embedding = embedding_model.encode(search_text)

    suggestie_collection.add(
        ids=[str(uuid.uuid4())],
        documents=[recipe_text],
        embeddings=[embedding.tolist()],
        metadatas=[{
            "ingredients" : ",".join(items),
            "kookniveau" : kookniveau,
            "kooktijd" : int(aantal_tijd),
            "liked": liked
        }]
    )

# %% [markdown]
# Tijd meten starten

# %%
for prompt in prompts:
    start_time = time.time()

# %% [markdown]
# MetaData opslaan

# %%
data = {
    "model": "nvidia/nemotron-3-nano-4b",
    "messages": [
        {"role": "user", "content": prompt}
    ],
    "temperature": 0.7
}


# %% [markdown]
# Bot functie

# %%
url = 'http://127.0.0.1:1234/v1/chat/completions'



def lmbot():
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()

        end_time = time.time()

        result = response.json()

        answer = result["choices"][0]["message"]["content"]
        model_name = result.get("model", "onbekend")
        response_length = len(answer)

    except requests.exceptions.RequestException as e:
        print(f"Fout bij API-aanroep: {e}")
        return ""

    regels = []

    for regel in answer.splitlines():
        if "nieuw ingredient" in regel.lower():
            ingredient = regel.split("=", 1)[1].strip()
            ingredient = ingredient.strip("()[]{}")
            ingredient = ingredient.replace(" ", "+")

            url2 = supermarkt + ingredient
            regel += f"|{url2}"

        regels.append(regel)

    return "\n".join(regels)

# %% [markdown]
# uitvoeren van de eerste stap van de agent

# %%
while True:
    bot = lmbot()

    print(bot)
    
    check = input("Zit hier een goed gerecht tussen? (Ja/Nee)")

    if check.lower() == "ja":
       
        for regel in bot.splitlines():
            save_suggestion(regel, liked=True)

        break
    
    else:

        for regel in bot.splitlines():
            save_suggestion(regel, liked=False)


# %% [markdown]
# Hele geselecteerde recept uitprinten

# %%
recept_nummer = int(input("Welk nummer van recept wil je hebben? "))

for regel in bot.splitlines():
    if regel.startswith(f"{recept_nummer} |"):
        recept_select = regel
        break

recept_prompt = f"""
    maak een volledig recept voor:
    
    {recept_select}

    Geef:
    -Ingrediënten
    -bereidingswijze
    -kooktijd,
    -aantal personen
    -kookspullen
    """


for prompt in recept_prompt:
    start_time = time.time()

data = {
    "model": "nvidia/nemotron-3-nano-4b",
    "messages": [
        {"role": "user", "content": recept_prompt}
    ],
    "temperature": 0.7
}

bot = lmbot()
print(bot)

full_recipe = bot
save_full_recipe(full_recipe)

# %% [markdown]
# Supermarkt route

# %%
boy = input('Wil je een kaart naar de supermarkt in de buurt (ja/nee)')

if boy.lower() == 'ja':
    if destination in ("niks", ""):
        url2 = (
            f"https://www.google.com/maps/dir/?api=1"
            f"&origin={lat},{lon}"
            f"&destination=supermarkt"
            f"&travelmode=driving"
        )
        webbrowser.open(url2)

    else:
        url2 = (
            f"https://www.google.com/maps/dir/?api=1"
            f"&origin={lat},{lon}"
            f"&destination={destination}"
            f"&travelmode=driving"
        )

        webbrowser.open(url2)
else:
    exit()


