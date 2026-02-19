"""
Servicio para Azure OpenAI con GPT-4o-mini
Motor de razonamiento e inteligencia del agente
Optimizado para bajo costo y respuestas concretas
"""

import os
import logging
import json
import re
from typing import List, Dict, Any, Optional
from openai import AzureOpenAI


class OpenAIService:
    """Servicio para Azure OpenAI (GPT-4o-mini)"""

    def __init__(self):
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.key = os.getenv("AZURE_OPENAI_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")

        if not self.endpoint or not self.key:
            raise ValueError("AZURE_OPENAI_ENDPOINT y AZURE_OPENAI_KEY/AZURE_OPENAI_API_KEY son requeridos")

        # Cliente de Azure OpenAI
        self.client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.key,
            api_version=self.api_version
        )

        logging.info(f"✅ OpenAIService inicializado: {self.deployment}")

    def analyze_opportunity(
        self,
        opportunity_text: str,
        available_teams: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Analiza una oportunidad de Dynamics 365 con razonamiento profundo

        Args:
            opportunity_text: Texto formateado de la oportunidad
            available_teams: Equipos disponibles con sus habilidades

        Returns:
            Diccionario con el análisis completo
        """
        try:
            logging.info("🧠 Iniciando análisis de oportunidad con IA...")

            # Preparar contexto de equipos
            teams_context = self._format_teams_context(available_teams)

            prompt = f"""Eres un experto analista de oportunidades comerciales y propuestas técnicas empresariales.
Analiza la siguiente oportunidad en profundidad y genera un análisis completo para apoyar la toma de decisiones comerciales y técnicas.

OPORTUNIDAD:
{opportunity_text[:25000]}

EQUIPOS/TORRES DISPONIBLES:
{teams_context}

INSTRUCCIONES:
Analiza la oportunidad siguiendo este formato JSON EXACTO:

{{
  "executive_summary": "Resumen ejecutivo conciso del análisis (3-4 párrafos). Incluye: qué solicita el cliente, complejidad estimada, viabilidad y recomendación general.",

  "key_requirements": ["Requerimiento clave 1", "Requerimiento clave 2", "Requerimiento clave 3"],

  "technical_assessment": "Evaluación técnica detallada. Qué implica técnicamente este proyecto, qué arquitectura podría necesitar, qué consideraciones técnicas son importantes.",

  "technology_stack": {{
    "frontend": ["tecnologías frontend identificadas o sugeridas"],
    "backend": ["tecnologías backend"],
    "databases": ["bases de datos"],
    "cloud": ["servicios cloud Azure, AWS, etc"],
    "ai_ml": ["tecnologías IA/ML si aplica"],
    "integrations": ["integraciones necesarias"],
    "other": ["otras tecnologías relevantes"]
  }},

  "required_towers": ["Torre TORRE1", "Torre TORRE2"],

  "team_recommendations": [
    {{
      "tower": "Torre NOMBRE",
      "team_name": "NOMBRE",
      "team_lead": "Nombre del líder",
      "team_lead_email": "email@ejemplo.com",
      "relevance_score": 0.85,
      "matched_skills": ["skill1", "skill2"],
      "justification": "Por qué este equipo es necesario para esta oportunidad",
      "estimated_involvement": "Full-time / Part-time / Consultoría"
    }}
  ],

  "risks": [
    {{
      "category": "Técnico/Comercial/Recursos/Timeline",
      "description": "Descripción del riesgo",
      "level": "Bajo/Medio/Alto/Crítico",
      "probability": 0.6,
      "impact": "Impacto potencial",
      "mitigation": "Estrategia de mitigación"
    }}
  ],
  "overall_risk_level": "Bajo/Medio/Alto",

  "timeline_estimate": {{
    "total_duration": "X-Y meses",
    "phases": [
      {{
        "phase_name": "Discovery & Diseño",
        "duration": "X semanas",
        "activities": ["Actividad 1", "Actividad 2"]
      }},
      {{
        "phase_name": "Desarrollo",
        "duration": "X meses",
        "activities": ["Actividad 1", "Actividad 2"]
      }},
      {{
        "phase_name": "Testing & QA",
        "duration": "X semanas",
        "activities": ["Actividad 1", "Actividad 2"]
      }},
      {{
        "phase_name": "Despliegue & Go-Live",
        "duration": "X semanas",
        "activities": ["Actividad 1", "Actividad 2"]
      }}
    ]
  }},

  "effort_estimate": {{
    "min_hours": 500,
    "max_hours": 800,
    "complexity": "Baja/Media/Alta/Muy Alta",
    "team_size_recommended": "X-Y personas",
    "assumptions": ["Asunción 1", "Asunción 2"]
  }},

  "recommendations": [
    "Recomendación estratégica o táctica 1",
    "Recomendación 2",
    "Recomendación 3"
  ],

  "clarification_questions": [
    "Pregunta que necesita aclaración del cliente 1",
    "Pregunta 2"
  ],

  "next_steps": [
    "Paso siguiente 1",
    "Paso siguiente 2",
    "Paso siguiente 3"
  ],

  "analysis_confidence": 0.80
}}

REGLAS IMPORTANTES:
1. Responde SOLO con el JSON, sin texto adicional antes o después
2. Para "required_towers", USA EXACTAMENTE los nombres de torre de la lista de equipos disponibles (ejemplo: "Torre IA", "Torre DATA")
3. Para cada equipo recomendado, COPIA EXACTAMENTE: team_lead, team_lead_email del equipo correspondiente
4. Sé realista con las estimaciones basándote en la complejidad descrita
5. Identifica riesgos reales y mitigaciones prácticas
6. Las preguntas de clarificación deben ayudar a refinar la propuesta
7. El equipo de QA (Torre Quality Assurance) y PMO (Torre PMO) son OBLIGATORIOS en proyectos medianos/grandes
"""

            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": "Eres un analista experto en oportunidades comerciales y propuestas técnicas empresariales."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=12000
            )

            result_text = response.choices[0].message.content.strip()

            logging.info(f"📝 Respuesta recibida: {len(result_text)} caracteres")

            # Extraer JSON de la respuesta
            result_json = self._extract_json(result_text)

            if result_json:
                logging.info("✅ Análisis de oportunidad completado con éxito")
                return result_json
            else:
                logging.error("❌ No se pudo parsear el JSON de la respuesta")
                logging.error(f"❌ Primeros 1000 caracteres: {result_text[:1000]}")
                return None

        except Exception as e:
            logging.error(f"❌ Error en análisis con IA: {str(e)}")
            import traceback
            logging.error(f"❌ Traceback: {traceback.format_exc()}")
            return None

    def _format_teams_context(self, teams: List[Dict[str, Any]]) -> str:
        """Formatea el contexto de equipos para el prompt"""
        lines = []
        for team in teams:
            # Manejar diferentes estructuras de datos
            name = team.get('team_name') or team.get('name', 'N/A')
            tower = team.get('tower', 'N/A')
            leader = team.get('team_lead') or team.get('leader', 'N/A')
            email = team.get('team_lead_email') or team.get('leader_email', 'N/A')
            skills = team.get('skills', [])
            description = team.get('description', 'N/A')

            lines.append(f"- {name} ({tower})")
            lines.append(f"  ID: {team.get('id', 'N/A')}")
            lines.append(f"  Líder: {leader}")
            lines.append(f"  Email: {email}")
            if skills:
                lines.append(f"  Skills: {', '.join(skills[:10])}")  # Limitar skills
            lines.append(f"  Descripción: {description}")
            lines.append("")
        return "\n".join(lines)

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extrae JSON de una respuesta que puede contener texto adicional"""
        try:
            # Intentar parsear directo
            return json.loads(text)
        except BaseException:
            pass

        # Remover tags de razonamiento de DeepSeek-R1 si existen
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        text = text.strip()

        # Buscar bloque de código JSON
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except BaseException:
                pass

        # Buscar bloque de código sin especificar lenguaje
        json_match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except BaseException:
                pass

        # Buscar primer { hasta último }
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            try:
                json_text = text[start:end + 1]
                return json.loads(json_text)
            except Exception as e:
                logging.error(f"❌ Error parseando JSON extraído: {str(e)}")

        return None
