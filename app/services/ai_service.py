import json
import time
import logging
from typing import List, Optional
from groq import Groq, GroqError

from app.config import settings
from app.models import Ticket, KBArticle
from app.schemas import AITriageResult, AICustomerReply

logger = logging.getLogger("service_desk.ai")


class AIService:
    """Service layer encapsulating Groq AI API calls for ticket triage and customer communication."""

    @staticmethod
    def _get_client() -> Optional[Groq]:
        """Initialize Groq client if API key is present."""
        api_key = settings.GROQ_API_KEY
        if not api_key or api_key.strip() in ["", "gsk_your_groq_api_key_here"]:
            logger.warning("GROQ_API_KEY is not configured in .env file.")
            return None
        try:
            return Groq(api_key=api_key.strip())
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            return None

    @staticmethod
    def analyze_ticket(ticket: Ticket, kb_articles: List[KBArticle]) -> Optional[AITriageResult]:
        """
        Analyze support ticket using Groq LLM and matched Knowledge Base articles.
        Returns a strongly typed AITriageResult or None if API fails/unavailable.
        """
        client = AIService._get_client()
        if not client:
            logger.warning("Groq AI client unavailable. Skipping AI analysis.")
            return None

        # Build KB context
        kb_context_items = []
        for i, kb in enumerate(kb_articles[:5], start=1):
            kb_context_items.append(
                f"--- KB Article #{i} [{kb.category}] ---\n"
                f"Title: {kb.title}\n"
                f"Problem: {kb.problem}\n"
                f"Solution: {kb.solution}\n"
            )
        kb_context = "\n".join(kb_context_items) if kb_context_items else "No specific matching KB articles found."

        system_prompt = (
            "You are a Senior IT Service Desk Engineer AI Co-Pilot. "
            "Your task is to analyze user-submitted technical support tickets, determine the probable root cause, "
            "provide step-by-step troubleshooting actions, suggest a resolution based on the Knowledge Base, "
            "and recommend the correct Category and Priority.\n\n"
            "CRITICAL INSTRUCTION: You MUST return ONLY a valid JSON object matching the required schema. "
            "Do NOT include markdown formatting (like ```json), commentary, or explanations outside the JSON object."
        )

        user_prompt = f"""
Analyze the following IT support ticket using the provided Knowledge Base articles for context.

--- SUPPORT TICKET DETAILS ---
Ticket ID: TCK-{ticket.id:04d}
Current Title: {ticket.title}
Current Category: {ticket.category}
Current Priority: {ticket.priority}
Description: {ticket.description}

--- RELEVANT KNOWLEDGE BASE CONTEXT ---
{kb_context}

--- REQUIRED JSON OUTPUT SCHEMA ---
Return a single JSON object with these exact keys:
{{
  "summary": "Concise 1-2 sentence overview of the issue",
  "recommended_category": "One of: Network & VPN, Access Management, Laptop / Endpoint, Email & Collaboration, Printers & Devices, Security, ERP / WMS, Telephony",
  "recommended_priority": "One of: Low, Medium, High, Urgent",
  "root_cause": "Technically accurate probable root cause analysis",
  "troubleshooting_steps": [
    "Step 1: First diagnostic or fix action",
    "Step 2: Second action",
    "Step 3: Third action"
  ],
  "suggested_resolution": "Detailed step-by-step resolution guide for the engineer",
  "confidence": 85,
  "difficulty": "One of: Easy, Medium, Hard, Complex"
}}
"""

        start_time = time.time()
        try:
            logger.info(f"Triggering Groq AI Triage for Ticket #{ticket.id} using model '{settings.GROQ_MODEL}'...")
            
            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
                max_tokens=1000
            )

            elapsed_ms = int((time.time() - start_time) * 1000)
            raw_content = response.choices[0].message.content
            logger.info(f"Groq API call completed in {elapsed_ms}ms (Model: {settings.GROQ_MODEL}).")

            # Parse JSON
            data = json.loads(raw_content)
            result = AITriageResult(**data)
            return result

        except GroqError as ge:
            logger.error(f"Groq API Error during ticket triage: {ge}")
            return None
        except json.JSONDecodeError as je:
            logger.error(f"Failed to parse JSON from Groq response: {je}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during AI analysis: {e}", exc_info=True)
            return None

    @staticmethod
    def generate_customer_reply(ticket: Ticket, resolution_text: Optional[str] = None) -> Optional[AICustomerReply]:
        """
        Generate a friendly, professional, non-technical email response for the end user.
        """
        client = AIService._get_client()
        if not client:
            logger.warning("Groq AI client unavailable. Cannot generate customer reply.")
            return None

        status_context = f"Resolution Details: {resolution_text or ticket.final_resolution or ticket.suggested_resolution or 'Issue investigated and fix applied.'}"

        system_prompt = (
            "You are an empathetic, professional IT Customer Support Specialist. "
            "Write a clear, non-technical, friendly email update to a customer regarding their support ticket.\n\n"
            "Return ONLY a valid JSON object with keys 'greeting', 'body', 'closing', and 'full_reply'."
        )

        user_prompt = f"""
Write a polite customer email update for the following ticket:

Ticket Title: {ticket.title}
Status: {ticket.status}
Technical Details: {status_context}

Output format JSON:
{{
  "greeting": "Dear Customer,",
  "body": "Friendly explanation of what was fixed or current status in simple non-technical terms.",
  "closing": "Best regards,\\nIT Support Team",
  "full_reply": "Combined full email text."
}}
"""

        try:
            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=500
            )

            raw_content = response.choices[0].message.content
            data = json.loads(raw_content)
            return AICustomerReply(**data)

        except Exception as e:
            logger.error(f"Error generating customer reply via Groq: {e}")
            return None
