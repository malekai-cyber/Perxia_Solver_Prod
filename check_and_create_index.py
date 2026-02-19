#!/usr/bin/env python3
"""
Script para verificar y crear el índice de Azure AI Search
Este script escribe los resultados en un archivo de log para asegurar visibilidad
"""
import requests
import json
import sys
import os
from datetime import datetime

# Configuración
SEARCH_ENDPOINT = "https://search-analyzer-prod.search.windows.net"
SEARCH_KEY = os.environ.get("AZURE_SEARCH_ADMIN_KEY", "<TU_SEARCH_KEY>")
INDEX_NAME = "torres-index"
API_VERSION = "2024-07-01"
LOG_FILE = "index_operations.log"


def log_message(message):
    """Escribe mensaje en archivo de log y en consola"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_entry + "\n")


def check_index_exists():
    """Verifica si el índice existe y cuenta los documentos"""
    headers = {"api-key": SEARCH_KEY}

    try:
        # Verificar índice
        index_url = f"{SEARCH_ENDPOINT}/indexes/{INDEX_NAME}?api-version={API_VERSION}"
        response = requests.get(index_url, headers=headers)

        if response.status_code == 200:
            log_message(f"✅ Índice '{INDEX_NAME}' EXISTE")

            # Contar documentos
            count_url = f"{SEARCH_ENDPOINT}/indexes/{INDEX_NAME}/docs/$count?api-version={API_VERSION}"
            count_response = requests.get(count_url, headers=headers)

            if count_response.status_code == 200:
                doc_count = int(count_response.text)
                log_message(f"📊 Documentos en el índice: {doc_count}")
                return True, doc_count
            else:
                log_message(f"⚠️  Error al contar documentos: {count_response.status_code}")
                return True, 0

        elif response.status_code == 404:
            log_message(f"❌ Índice '{INDEX_NAME}' NO EXISTE")
            return False, 0
        else:
            log_message(f"❌ Error verificando índice: {response.status_code} - {response.text}")
            return False, 0

    except Exception as e:
        log_message(f"❌ Excepción verificando índice: {str(e)}")
        return False, 0


def delete_index():
    """Elimina el índice si existe"""
    headers = {"api-key": SEARCH_KEY}
    delete_url = f"{SEARCH_ENDPOINT}/indexes/{INDEX_NAME}?api-version={API_VERSION}"

    try:
        response = requests.delete(delete_url, headers=headers)
        if response.status_code in [200, 204]:
            log_message("🗑️  Índice eliminado exitosamente")
            return True
        elif response.status_code == 404:
            log_message("ℹ️  Índice no existía, no hay nada que eliminar")
            return True
        else:
            log_message(f"❌ Error eliminando índice: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        log_message(f"❌ Excepción eliminando índice: {str(e)}")
        return False


def create_index():
    """Crea el índice con el esquema correcto"""
    headers = {
        "Content-Type": "application/json",
        "api-key": SEARCH_KEY
    }

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
        ],
        "semantic": {
            "configurations": [
                {
                    "name": "torres-semantic-config",
                    "prioritizedFields": {
                        "contentFields": [{"fieldName": "description"}],
                        "keywordsFields": [{"fieldName": "skills"}, {"fieldName": "technologies"}]
                    }
                }
            ]
        }
    }

    create_url = f"{SEARCH_ENDPOINT}/indexes?api-version={API_VERSION}"

    try:
        response = requests.post(create_url, headers=headers, json=index_schema)
        if response.status_code in [200, 201]:
            log_message("✅ Índice creado exitosamente")
            return True
        else:
            log_message(f"❌ Error creando índice: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        log_message(f"❌ Excepción creando índice: {str(e)}")
        return False


def upload_documents():
    """Carga los documentos de torres al índice"""
    headers = {
        "Content-Type": "application/json",
        "api-key": SEARCH_KEY
    }

    # Cargar datos de torres
    try:
        with open('data/torres_nuevas.json', 'r', encoding='utf-8') as f:
            torres_data = json.load(f)

        log_message(f"📂 Cargados {len(torres_data)} torres desde el archivo")

        # Preparar documentos para Azure Search
        documents = []
        for torre in torres_data:
            doc = {
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

        # Subir en batch
        upload_payload = {"value": [{"@search.action": "upload", **doc} for doc in documents]}
        upload_url = f"{SEARCH_ENDPOINT}/indexes/{INDEX_NAME}/docs/index?api-version={API_VERSION}"

        response = requests.post(upload_url, headers=headers, json=upload_payload)

        if response.status_code in [200, 201]:
            result = response.json()
            success_count = sum(1 for r in result.get('value', []) if r.get('status'))
            log_message(f"✅ Documentos cargados exitosamente: {success_count}/{len(documents)}")
            return True
        else:
            log_message(f"❌ Error cargando documentos: {response.status_code} - {response.text}")
            return False

    except FileNotFoundError:
        log_message("❌ Archivo de datos no encontrado: data/torres_nuevas.json")
        return False
    except json.JSONDecodeError:
        log_message("❌ Error parsing JSON del archivo de torres")
        return False
    except Exception as e:
        log_message(f"❌ Excepción cargando documentos: {str(e)}")
        return False


def main():
    """Función principal"""
    log_message("=" * 70)
    log_message("INICIO DE OPERACIONES DE ÍNDICE")
    log_message("=" * 70)

    # Paso 1: Verificar estado actual
    log_message("\n🔍 PASO 1: Verificando estado del índice...")
    exists, doc_count = check_index_exists()

    # Paso 2: Decidir acción
    if exists and doc_count == 13:
        log_message("\n✅ El índice ya está correcto con 13 documentos. No se requiere acción.")
        log_message("=" * 70)
        return 0

    if exists:
        log_message(f"\n🔄 PASO 2: Índice existe pero tiene {doc_count} documentos (se esperan 13)")
        log_message("Eliminando índice para recrearlo...")
        if not delete_index():
            log_message("❌ Falló la eliminación del índice. Abortando.")
            return 1
        import time
        time.sleep(2)  # Esperar a que Azure procese la eliminación

    # Paso 3: Crear índice
    log_message("\n🏗️  PASO 3: Creando índice...")
    if not create_index():
        log_message("❌ Falló la creación del índice. Abortando.")
        return 1

    import time
    time.sleep(2)  # Esperar a que el índice esté listo

    # Paso 4: Cargar documentos
    log_message("\n📤 PASO 4: Cargando documentos...")
    if not upload_documents():
        log_message("❌ Falló la carga de documentos. Abortando.")
        return 1

    import time
    time.sleep(2)  # Esperar indexación

    # Paso 5: Verificar resultado final
    log_message("\n✅ PASO 5: Verificando resultado final...")
    exists_final, doc_count_final = check_index_exists()

    if exists_final and doc_count_final == 13:
        log_message("\n🎉 ¡ÉXITO! Índice creado y cargado correctamente con 13 documentos")
    else:
        log_message(f"\n⚠️  Índice creado pero tiene {doc_count_final} documentos (se esperaban 13)")

    log_message("=" * 70)
    log_message(f"FIN DE OPERACIONES - Ver detalles en {LOG_FILE}")
    log_message("=" * 70)

    return 0 if doc_count_final == 13 else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        log_message("\n⚠️  Operación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        log_message(f"\n❌ Error inesperado: {str(e)}")
        sys.exit(1)
