import requests
import json
import time
import os

print("=" * 70)
print("CREANDO ÍNDICE DE AZURE AI SEARCH")
print("=" * 70)

SEARCH_ENDPOINT = "https://search-analyzer-prod.search.windows.net"
SEARCH_KEY = os.environ.get("AZURE_SEARCH_ADMIN_KEY", "<TU_SEARCH_KEY>")
INDEX_NAME = "torres-index"
API_VERSION = "2024-07-01"

headers = {
    "Content-Type": "application/json",
    "api-key": SEARCH_KEY
}

# PASO 1: Eliminar índice si existe
print("\nPASO 1: Eliminando índice existente (si existe)...")
delete_url = f"{SEARCH_ENDPOINT}/indexes/{INDEX_NAME}?api-version={API_VERSION}"
r = requests.delete(delete_url, headers={"api-key": SEARCH_KEY})
print(f"Status de eliminación: {r.status_code}")
if r.status_code in [200, 204]:
    print("✅ Índice eliminado")
elif r.status_code == 404:
    print("ℹ️  Índice no existía")
time.sleep(2)

# PASO 2: Crear nuevo índice
print("\nPASO 2: Creando índice...")
index_schema = {
    "name": INDEX_NAME,
    "fields": [
        {"name": "id", "type": "Edm.String", "key": True, "searchable": False},
        {"name": "tower", "type": "Edm.String", "searchable": True, "filterable": True, "sortable": True},
        {"name": "team_lead", "type": "Edm.String", "searchable": True},
        {"name": "team_lead_email", "type": "Edm.String", "searchable": False, "filterable": True},
        {"name": "skills", "type": "Collection(Edm.String)", "searchable": True, "filterable": True},
        {"name": "technologies", "type": "Collection(Edm.String)", "searchable": True, "filterable": True},
        {"name": "expertise_areas", "type": "Collection(Edm.String)", "searchable": True, "filterable": True},
        {"name": "frameworks", "type": "Collection(Edm.String)", "searchable": True, "filterable": True},
        {"name": "description", "type": "Edm.String", "searchable": True}
    ]
}

create_url = f"{SEARCH_ENDPOINT}/indexes?api-version={API_VERSION}"
r = requests.post(create_url, headers=headers, json=index_schema)
print(f"Status de creación: {r.status_code}")
if r.status_code in [200, 201]:
    print("✅ Índice creado exitosamente")
else:
    print(f"❌ Error: {r.text}")
    exit(1)
time.sleep(2)

# PASO 3: Cargar documentos
print("\nPASO 3: Cargando documentos de torres...")
with open('data/torres_nuevas.json', 'r', encoding='utf-8') as f:
    torres_data = json.load(f)

print(f"Documentos a cargar: {len(torres_data)}")

documents = []
for torre in torres_data:
    doc = {
        "@search.action": "upload",
        "id": torre["tower"].lower().replace(" ", "_"),
        "tower": torre["tower"],
        "team_lead": torre["team_lead"],
        "team_lead_email": torre["team_lead_email"],
        "skills": torre["skills"],
        "technologies": torre["technologies"],
        "expertise_areas": torre["expertise_areas"],
        "frameworks": torre.get("frameworks", []),
        "description": torre["description"]
    }
    documents.append(doc)

upload_payload = {"value": documents}
upload_url = f"{SEARCH_ENDPOINT}/indexes/{INDEX_NAME}/docs/index?api-version={API_VERSION}"
r = requests.post(upload_url, headers=headers, json=upload_payload)
print(f"Status de carga: {r.status_code}")

if r.status_code in [200, 201]:
    result = r.json()
    success_count = sum(1 for item in result.get('value', []) if item.get('status'))
    print(f"✅ Documentos cargados: {success_count}/{len(documents)}")
else:
    print(f"❌ Error cargando documentos: {r.text}")
    exit(1)

time.sleep(3)

# PASO 4: Verificar
print("\nPASO 4: Verificando índice...")
count_url = f"{SEARCH_ENDPOINT}/indexes/{INDEX_NAME}/docs/$count?api-version={API_VERSION}"
r = requests.get(count_url, headers={"api-key": SEARCH_KEY})
if r.status_code == 200:
    count = int(r.text)
    print(f"📊 Documentos en el índice: {count}")
    if count == 13:
        print("\n🎉 ¡ÉXITO! Índice creado correctamente con 13 torres")
    else:
        print(f"\n⚠️  Se esperaban 13 documentos, se encontraron {count}")
else:
    print(f"❌ Error verificando: {r.status_code}")

print("\n" + "=" * 70)
print("PROCESO COMPLETADO")
print("=" * 70)
