"""
🎨 Generador de Adaptive Cards para Oportunidades - Diseño Profesional
Compatible con Microsoft Teams
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime


def _get_risk_icon(risk_level: str) -> str:
    """Retorna el icono apropiado según el nivel de riesgo"""
    risk_level = (risk_level or "").lower()
    if risk_level in ['alto', 'high', 'crítico', 'critical']:
        return "🔴"
    elif risk_level in ['medio', 'medium', 'moderado', 'moderate']:
        return "🟡"
    else:
        return "🟢"


def _get_tower_icon(tower: str) -> str:
    """Retorna el icono apropiado para cada torre organizacional"""
    tower_lower = (tower or "").lower()
    icons = {
        'fullstack': '💻', 'full-stack': '💻', 'full stack': '💻',
        'data': '📊', 'analytics': '📈', 'bi': '📉',
        'ciberseguridad': '🔒', 'cybersecurity': '🔒', 'security': '🔐',
        'ia': '🤖', 'ai': '🤖', 'ml': '🧠',
        'rpa': '⚙️', 'automation': '🔄',
        'cloud': '☁️', 'devops': '🚀',
        'mobile': '📱', 'qa': '✅', 'testing': '🧪',
        'sap': '📦', 'integracion': '🔗', 'integration': '🔗',
        'portales': '🌐', 'soporte': '🛠️', 'mantenimiento': '🔧',
        'pmo': '📋', 'management': '📋'
    }
    
    for key, icon in icons.items():
        if key in tower_lower:
            return icon
    return '🏢'


def _truncate_text(text: str, max_length: int = 500) -> str:
    """Trunca texto de forma segura"""
    if not text:
        return ""
    text = str(text)
    if len(text) > max_length:
        return text[:max_length - 3] + "..."
    return text


def generate_opportunity_card(
    opportunity_id: str,
    opportunity_name: str,
    opportunity_url: str,
    analysis_data: Dict[str, Any],
    pdf_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Genera un Adaptive Card profesional para análisis de oportunidades
    
    Args:
        opportunity_id: ID de la oportunidad
        opportunity_name: Nombre de la oportunidad
        opportunity_url: URL de la oportunidad en Dynamics 365
        analysis_data: Datos del análisis de IA
        pdf_url: URL del PDF generado (opcional)
        
    Returns:
        Diccionario con el Adaptive Card
    """
    try:
        logging.info("🎨 Generando Adaptive Card para oportunidad...")
        
        # Validación de datos
        if not analysis_data:
            analysis_data = {}
        
        # Extraer datos del análisis
        exec_summary = _truncate_text(analysis_data.get("executive_summary", "Análisis en proceso"), 600)
        key_requirements = analysis_data.get("key_requirements", [])[:6]
        teams = analysis_data.get("team_recommendations", [])[:6]
        risks = analysis_data.get("risks", [])[:5]
        overall_risk = analysis_data.get("overall_risk_level", "Medio")
        timeline = analysis_data.get("timeline_estimate", {})
        effort = analysis_data.get("effort_estimate", {})
        recommendations = analysis_data.get("recommendations", [])[:5]
        next_steps = analysis_data.get("next_steps", [])[:5]
        clarification_questions = analysis_data.get("clarification_questions", [])[:4]
        confidence = analysis_data.get("analysis_confidence", 0.75)
        
        body = []
        
        # ========================================
        # 🎯 HEADER - Información Principal
        # ========================================
        body.append({
            "type": "Container",
            "style": "emphasis",
            "bleed": True,
            "items": [
                {
                    "type": "TextBlock",
                    "text": "🎯 Análisis Inteligente de Oportunidad",
                    "weight": "Bolder",
                    "size": "ExtraLarge",
                    "wrap": True,
                    "color": "Accent"
                },
                {
                    "type": "TextBlock",
                    "text": f"**{_truncate_text(opportunity_name, 150)}**",
                    "size": "Large",
                    "wrap": True
                },
                {
                    "type": "TextBlock",
                    "text": f"ID: {opportunity_id} • Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                    "size": "Small",
                    "isSubtle": True
                }
            ]
        })
        
        # ========================================
        # 📊 RESUMEN EJECUTIVO
        # ========================================
        body.append({
            "type": "Container",
            "items": [
                {
                    "type": "TextBlock",
                    "text": "📊 Resumen Ejecutivo",
                    "weight": "Bolder",
                    "size": "Medium",
                    "spacing": "Large"
                },
                {
                    "type": "TextBlock",
                    "text": exec_summary,
                    "wrap": True,
                    "size": "Small"
                }
            ]
        })
        
        # ========================================
        # 📋 REQUERIMIENTOS CLAVE
        # ========================================
        if key_requirements:
            req_items = [{"type": "TextBlock", "text": f"• {req}", "wrap": True, "size": "Small"} 
                        for req in key_requirements if req]
            if req_items:
                body.append({
                    "type": "Container",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "📋 Requerimientos Clave",
                            "weight": "Bolder",
                            "size": "Medium",
                            "spacing": "Medium"
                        }
                    ] + req_items
                })
        
        # ========================================
        # 👥 EQUIPOS RECOMENDADOS
        # ========================================
        if teams:
            team_columns = []
            for team in teams[:4]:
                if isinstance(team, dict):
                    tower = team.get("tower", "")
                    team_name = team.get("team_name", "")
                    score = team.get("relevance_score", 0)
                    score_pct = int(score * 100) if isinstance(score, (int, float)) else 0
                    
                    team_columns.append({
                        "type": "Column",
                        "width": "stretch",
                        "items": [
                            {
                                "type": "TextBlock",
                                "text": f"{_get_tower_icon(tower)} **{team_name}**",
                                "wrap": True,
                                "size": "Small"
                            },
                            {
                                "type": "TextBlock",
                                "text": f"Match: {score_pct}%",
                                "size": "Small",
                                "isSubtle": True
                            }
                        ]
                    })
            
            if team_columns:
                body.append({
                    "type": "Container",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "👥 Equipos Recomendados",
                            "weight": "Bolder",
                            "size": "Medium",
                            "spacing": "Medium"
                        },
                        {
                            "type": "ColumnSet",
                            "columns": team_columns[:2]
                        }
                    ] + ([{"type": "ColumnSet", "columns": team_columns[2:4]}] if len(team_columns) > 2 else [])
                })
        
        # ========================================
        # ⚠️ EVALUACIÓN DE RIESGOS
        # ========================================
        if risks or overall_risk:
            risk_items = [{
                "type": "TextBlock",
                "text": f"{_get_risk_icon(overall_risk)} Nivel General: **{overall_risk}**",
                "wrap": True
            }]
            
            for risk in risks[:3]:
                if isinstance(risk, dict):
                    level = risk.get("level", "")
                    desc = _truncate_text(risk.get("description", ""), 150)
                    risk_items.append({
                        "type": "TextBlock",
                        "text": f"{_get_risk_icon(level)} {desc}",
                        "wrap": True,
                        "size": "Small"
                    })
            
            body.append({
                "type": "Container",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": "⚠️ Evaluación de Riesgos",
                        "weight": "Bolder",
                        "size": "Medium",
                        "spacing": "Medium"
                    }
                ] + risk_items
            })
        
        # ========================================
        # ⏱️ ESTIMACIÓN
        # ========================================
        if timeline or effort:
            est_items = []
            if timeline.get("total_duration"):
                est_items.append({
                    "type": "TextBlock",
                    "text": f"⏱️ **Duración estimada:** {timeline['total_duration']}",
                    "wrap": True
                })
            
            if effort:
                min_h = effort.get("min_hours", 0)
                max_h = effort.get("max_hours", 0)
                complexity = effort.get("complexity", "")
                if min_h and max_h:
                    est_items.append({
                        "type": "TextBlock",
                        "text": f"💪 **Esfuerzo:** {min_h}-{max_h} horas ({complexity})",
                        "wrap": True
                    })
            
            if est_items:
                body.append({
                    "type": "Container",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "📈 Estimación",
                            "weight": "Bolder",
                            "size": "Medium",
                            "spacing": "Medium"
                        }
                    ] + est_items
                })
        
        # ========================================
        # 💡 RECOMENDACIONES
        # ========================================
        if recommendations:
            rec_items = [{"type": "TextBlock", "text": f"💡 {rec}", "wrap": True, "size": "Small"} 
                        for rec in recommendations if rec]
            if rec_items:
                body.append({
                    "type": "Container",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "💡 Recomendaciones",
                            "weight": "Bolder",
                            "size": "Medium",
                            "spacing": "Medium"
                        }
                    ] + rec_items[:4]
                })
        
        # ========================================
        # ❓ PREGUNTAS DE CLARIFICACIÓN
        # ========================================
        if clarification_questions:
            q_items = [{"type": "TextBlock", "text": f"❓ {q}", "wrap": True, "size": "Small"} 
                      for q in clarification_questions if q]
            if q_items:
                body.append({
                    "type": "Container",
                    "style": "warning",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "❓ Puntos a Clarificar",
                            "weight": "Bolder",
                            "size": "Medium"
                        }
                    ] + q_items[:3]
                })
        
        # ========================================
        # 🎯 PRÓXIMOS PASOS
        # ========================================
        if next_steps:
            step_items = [{"type": "TextBlock", "text": f"→ {step}", "wrap": True, "size": "Small"} 
                         for step in next_steps if step]
            if step_items:
                body.append({
                    "type": "Container",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "🎯 Próximos Pasos",
                            "weight": "Bolder",
                            "size": "Medium",
                            "spacing": "Medium"
                        }
                    ] + step_items[:4]
                })
        
        # ========================================
        # 🔗 ACCIONES
        # ========================================
        actions = []
        
        if opportunity_url:
            actions.append({
                "type": "Action.OpenUrl",
                "title": "🔗 Ver en Dynamics 365",
                "url": opportunity_url
            })
        
        if pdf_url:
            actions.append({
                "type": "Action.OpenUrl",
                "title": "📄 Descargar PDF",
                "url": pdf_url
            })
        
        # ========================================
        # 📊 FOOTER - Confianza del Análisis
        # ========================================
        confidence_pct = int(confidence * 100) if isinstance(confidence, (int, float)) else 75
        body.append({
            "type": "Container",
            "separator": True,
            "spacing": "Medium",
            "items": [
                {
                    "type": "TextBlock",
                    "text": f"🤖 Confianza del análisis: {confidence_pct}% • Modelo: DeepSeek-R1",
                    "size": "Small",
                    "isSubtle": True,
                    "horizontalAlignment": "Right"
                }
            ]
        })
        
        # ========================================
        # 🎴 CONSTRUIR CARD FINAL
        # ========================================
        card = {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.5",
            "body": body
        }
        
        if actions:
            card["actions"] = actions
        
        logging.info("✅ Adaptive Card generado exitosamente")
        return card
        
    except Exception as e:
        logging.error(f"❌ Error generando Adaptive Card: {str(e)}")
        # Retornar card de error
        return {
            "type": "AdaptiveCard",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.5",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "⚠️ Error generando visualización",
                    "weight": "Bolder",
                    "color": "Attention"
                },
                {
                    "type": "TextBlock",
                    "text": f"Oportunidad: {opportunity_name}",
                    "wrap": True
                },
                {
                    "type": "TextBlock",
                    "text": str(e),
                    "size": "Small",
                    "isSubtle": True
                }
            ]
        }
