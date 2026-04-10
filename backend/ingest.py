import json, chromadb, ollama
from tqdm import tqdm
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

client = chromadb.PersistentClient(path=str(BASE_DIR / "vectorstore"))
collection = client.get_or_create_collection("mtg_cards")

with open(BASE_DIR / "data" / "scryfall_cards.json", encoding="utf-8") as f:
    cards = json.load(f)

def get_card_fields(card):
    faces = card.get("card_faces")
    if faces:
        return {
            "oracle_text": " // ".join(f.get("oracle_text", "") for f in faces),
            "type_line":   " // ".join(f.get("type_line", "") for f in faces),
            "mana_cost":   " // ".join(f.get("mana_cost", "") for f in faces),
        }
    return {
        "oracle_text": card.get("oracle_text", ""),
        "type_line":   card.get("type_line", ""),
        "mana_cost":   card.get("mana_cost", ""),
    }

def build_doc(card):
    fields    = get_card_fields(card)
    keywords  = ", ".join(card.get("keywords") or [])
    legal_in  = [f for f, v in (card.get("legalities") or {}).items() if v == "legal"]
    banned_in = [f for f, v in (card.get("legalities") or {}).items() if v == "banned"]

    pt = ""
    if card.get("power"):
        pt = f"Power/Toughness: {card['power']}/{card['toughness']}\n"
    elif card.get("loyalty"):
        pt = f"Loyalty: {card['loyalty']}\n"

    return (
        f"Name: {card.get('name', '')}\n"
        f"Mana Cost: {fields['mana_cost']} (CMC {card.get('cmc', 0)})\n"
        f"Type: {fields['type_line']}\n"
        f"Rarity: {card.get('rarity', '')}\n"
        f"{pt}"
        f"Rules Text: {fields['oracle_text']}\n"
        f"Keywords: {keywords}\n"
        f"Legal in: {', '.join(legal_in)}\n"
        f"Banned in: {', '.join(banned_in)}\n"
        f"Set: {card.get('set_name', '')}"
    )

# # Find an MDFC
# mdfc = next(c for c in cards if c.get("layout") == "modal_dfc")
# print(build_doc(mdfc))


BATCH = 256
SKIP_LAYOUTS = {"art_series", "token", "emblem", "scheme", "vanguard", "planar"}
for i in tqdm(range(0, len(cards), BATCH)):
    batch = cards[i:i+BATCH]
    ids, docs, metadatas = [], [], []

    for card in batch:
        if card.get("layout") in SKIP_LAYOUTS:
            continue

        fields = get_card_fields(card)
        ids.append(card.get("oracle_id") or card["id"])
        docs.append(build_doc(card))
        metadatas.append({
            "name":        card.get("name", ""),
            "mana_cost":   fields["mana_cost"],
            "type_line":   fields["type_line"],
            "colors":      str(card.get("colors", [])),
            "cmc":         str(card.get("cmc", 0)),
            "oracle_tags": "|".join(card.get("oracle_tags") or []),
            "art_tags":    "|".join(card.get("art_tags") or []),
            "rarity":    card.get("rarity", ""),
            "set_name":  card.get("set_name", ""),
            "digital":   str(card.get("digital", False)),
        })

    embeddings = [
        ollama.embeddings(model="mxbai-embed-large", prompt=doc)["embedding"]
        for doc in docs
    ]
    collection.upsert(ids=ids, documents=docs,
                      metadatas=metadatas, embeddings=embeddings)

print(f"Ingested {len(cards)} cards.")