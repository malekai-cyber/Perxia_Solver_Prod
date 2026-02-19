import requests
import os

# Configuración
search_endpoint = "https://search-analyzer-prod.search.windows.net"
search_key = os.environ.get("AZURE_SEARCH_ADMIN_KEY", "<TU_SEARCH_KEY>")
index_name = "torres-index"

headers = {
    "Content-Type": "application/json",
    "api-key": search_key
}

# Verificar si el índice existe
print(f"\n{'=' * 60}")
print(f"VERIFICANDO ÍNDICE: {index_name}")
print(f"{'=' * 60}\n")

try:
    # Verificar índice
    index_url = f"{search_endpoint}/indexes/{index_name}?api-version=2024-07-01"
    response = requests.get(index_url, headers=headers)

    if response.status_code == 200:
        print("✅ El índice EXISTE")
        index_data = response.json()
        print(f"   Nombre: {index_data.get('name')}")
        print(f"   Campos: {len(index_data.get('fields', []))}")

        # Contar documentos
        count_url = f"{search_endpoint}/indexes/{index_name}/docs/$count?api-version=2024-07-01"
        count_response = requests.get(count_url, headers=headers)

        if count_response.status_code == 200:
            doc_count = int(count_response.text)
            print(f"   Documentos: {doc_count}")

            if doc_count == 0:
                print("\n⚠️  EL ÍNDICE ESTÁ VACÍO - Necesita datos")
            elif doc_count == 13:
                print("\n✅ EL ÍNDICE TIENE TODOS LOS DOCUMENTOS ESPERADOS (13 torres)")
            else:
                print(f"\n⚠️  El índice tiene {doc_count} documentos, se esperaban 13")

            # Mostrar algunos documentos
            if doc_count > 0:
                search_url = f"{search_endpoint}/indexes/{index_name}/docs?api-version=2024-07-01&$top=3"
                docs_response = requests.get(search_url, headers=headers)
                if docs_response.status_code == 200:
                    docs = docs_response.json()
                    print("\n📄 Primeros documentos:")
                    for doc in docs.get('value', [])[:3]:
                        print(f"   - {doc.get('tower', 'N/A')} ({doc.get('id', 'N/A')})")
        else:
            print(f"   ⚠️  No se pudo contar documentos: {count_response.status_code}")

    elif response.status_code == 404:
        print("❌ EL ÍNDICE NO EXISTE - Necesita ser creado")
    else:
        print(f"❌ Error al verificar índice: {response.status_code}")
        print(f"   Respuesta: {response.text}")

except Exception as e:
    print(f"❌ Error de conexión: {str(e)}")

print(f"\n{'=' * 60}\n")
