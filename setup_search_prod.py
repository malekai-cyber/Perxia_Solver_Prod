"""
Script simple para crear el índice de Azure AI Search en PRODUCCIÓN
"""

import json
import os
import requests

# Configuración PRODUCCIÓN
SEARCH_ENDPOINT = "https://search-analyzer-prod.search.windows.net"
SEARCH_KEY = os.environ.get("AZURE_SEARCH_ADMIN_KEY", "<TU_SEARCH_KEY>")
INDEX_NAME = "torres-index"
API_VERSION = "2024-07-01"


def create_index():
    """Crea el índice con schema básico"""
    url = f"{SEARCH_ENDPOINT}/indexes/{INDEX_NAME}?api-version={API_VERSION}"
    headers = {
        "Content-Type": "application/json",
        "api-key": SEARCH_KEY
    }

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

    response = requests.put(url, headers=headers, json=schema)
    if response.status_code in [200, 201]:
        print(f"✅ Índice '{INDEX_NAME}' creado exitosamente")
        return True
    else:
        print(f"❌ Error creating index: {response.status_code}")
        print(response.text)
        return False


def upload_torres():
    """Sube datos de torres al índice"""
    # Cargar datos de torres
    with open("data/torres_nuevas.json", "r", encoding="utf-8") as f:
        torres = json.load(f)

    # Preparar documentos para upload
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

    # Upload batch
    url = f"{SEARCH_ENDPOINT}/indexes/{INDEX_NAME}/docs/index?api-version={API_VERSION}"
    headers = {
        "Content-Type": "application/json",
        "api-key": SEARCH_KEY
    }

    payload = {"value": [{"@search.action": "mergeOrUpload", **doc} for doc in documents]}

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        print(f"✅ {len(documents)} torres subidas exitosamente")
        return True
    else:
        print(f"❌ Error uploading docs: {response.status_code}")
        print(response.text)
        return False


if __name__ == "__main__":
    print("🚀 Configurando Azure AI Search - PRODUCCIÓN")
    print(f"📍 Endpoint: {SEARCH_ENDPOINT}")
    print(f"📋 Índice: {INDEX_NAME}\n")

    if create_index():
        print()
        upload_torres()

    print("\n✅ Setup completado!")
