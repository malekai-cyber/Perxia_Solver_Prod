#!/usr/bin/env python3
"""
Test script para Azure Function AnalyzeOpportunity en PRODUCCIÓN
"""

import requests
import json
import os
from datetime import datetime

# Configuración PRODUCCIÓN
FUNCTION_URL = "https://func-analyzer-prod.azurewebsites.net/api/AnalyzeOpportunity"
API_KEY = os.environ.get("AZURE_FUNCTION_KEY", "<TU_FUNCTION_KEY>")


def test_analyze_opportunity():
    """Test básico de la función AnalyzeOpportunity"""

    # Payload de ejemplo
    payload = {
        "opportunity_description": "Proyecto de análisis de datos con IA para optimización de procesos",
        "torres_needed": ["IA", "DATA"],
        "priority": "high",
        "client_name": "Acme Corp",
        "estimated_budget": 50000
    }

    # Headers
    headers = {
        "Content-Type": "application/json"
    }

    # URL con API Key
    url_with_key = f"{FUNCTION_URL}?code={API_KEY}"

    print("=" * 80)
    print("🔍 TEST: Azure Function - AnalyzeOpportunity (PRODUCCIÓN)")
    print("=" * 80)
    print(f"\n📍 URL: {FUNCTION_URL}")
    print(f"📅 Timestamp: {datetime.now().isoformat()}")
    print("\n📋 Payload:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    try:
        print("\n⏳ Enviando solicitud...")
        response = requests.post(url_with_key, json=payload, headers=headers, timeout=30)

        print(f"\n✅ Status Code: {response.status_code}")
        print(f"📝 Response Headers: {dict(response.headers)}")

        # Parsear respuesta
        try:
            data = response.json()
            print("\n📊 Response Body:")
            print(json.dumps(data, indent=2, ensure_ascii=False))

            # Verificar estructura
            if response.status_code == 200:
                if 'body' in data and 'outputs' in data['body']:
                    print("\n✅ Estructura correcta detectada")
                    if 'adaptive_card' in data['body']['outputs']:
                        print("✅ Adaptive Card presente")
                    if 'analysis' in data['body']:
                        print("✅ Análisis presente")
                else:
                    print("\n⚠️ Estructura diferente a la esperada")
        except BaseException:
            print(f"\n📄 Raw Response:\n{response.text}")

        return response.status_code == 200

    except requests.exceptions.Timeout:
        print("\n❌ Error: Timeout (30s)")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ Error de conexión: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = test_analyze_opportunity()
    print("\n" + "=" * 80)
    if success:
        print("✅ TEST EXITOSO")
    else:
        print("❌ TEST FALLIDO")
    print("=" * 80)
