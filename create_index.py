import requests
import json
import os

SEARCH_ENDPOINT = "https://search-analyzer-prod.search.windows.net"
SEARCH_KEY = os.environ.get("AZURE_SEARCH_ADMIN_KEY", "<TU_SEARCH_KEY>")
INDEX_NAME = "torres-index"
API_VERSION = "2024-07-01"

print("=== CREANDO ÍNDICE AZURE AI SEARCH ===")
print(f"Endpoint: {SEARCH_ENDPOINT}")
print(f"Índice: {INDEX_NAME}\n")

# 1. Crear índice
url = f"{SEARCH_ENDPOINT}/indexes/{INDEX_NAME}?api-version={API_VERSION}"
headers = {"Content-Type": "application/json", "api-key": SEARCH_KEY}

schema = {
    "name": INDEX_NAME,
    "fields": [
        {"name": "id", "type": "Edm.String", "key": True},
        {"name": "team_name", "type": "Edm.String", "searchable": True},
        {"name": "tower", "type": "Edm.String", "searchable": True, "filterable": True},
        {"name": "description", "type": "Edm.String", "searchable": True},
        {"name": "team_lead", "type": "Edm.String", "searchable": True},
        {"name": "team_lead_email", "type": "Edm.String"},
        {"name": "skills", "type": "Collection(Edm.String)", "searchable": True},
        {"name": "technologies", "type": "Collection(Edm.String)", "searchable": True},
        {"name": "expertise_areas", "type": "Collection(Edm.String)", "searchable": True}
    ]
}

print("1. Creando índice...")
r = requests.put(url, headers=headers, json=schema)
print(f"   Status: {r.status_code}")
if r.status_code in [200, 201]:
    print("   ✅ Índice creado\n")
else:
    print(f"   ⚠️  {r.text}\n")

# 2. Cargar torres
print("2. Cargando datos de torres...")
with open("data/torres_nuevas.json", "r", encoding="utf-8") as f:
    torres = json.load(f)

documents = []
for torre in torres:
    doc = {
        "id": torre["tower"].lower().replace(" ", "-"),
        "team_name": torre["tower"],
        "tower": torre["tower"],
        "description": torre.get("description", ""),
        "team_lead": torre["team_lead"],
        "team_lead_email": torre["team_lead_email"],
        "skills": torre.get("skills", []),
        "technologies": torre.get("technologies", []),
        "expertise_areas": torre.get("expertise_areas", [])
    }
    documents.append(doc)

print(f"   {len(documents)} torres encontradas")

# 3. Upload
url = f"{SEARCH_ENDPOINT}/indexes/{INDEX_NAME}/docs/index?api-version={API_VERSION}"
payload = {"value": [{"@search.action": "mergeOrUpload", **doc} for doc in documents]}

print("3. Subiendo documentos...")
r = requests.post(url, headers=headers, json=payload)
print(f"   Status: {r.status_code}")
if r.status_code in [200, 201]:
    result = r.json()
    success = sum(1 for item in result.get("value", []) if item.get("status"))
    print(f"   ✅ {success} torres subidas exitosamente\n")
else:
    print(f"   ❌ Error: {r.text}\n")

print("=== COMPLETADO ===")
