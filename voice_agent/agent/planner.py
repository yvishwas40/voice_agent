import os
import json
from groq import Groq
from dotenv import load_dotenv

from .schemas import PlannerOutput, AgentState
from ..utils.logger import logger

load_dotenv()

SYSTEM_PROMPT = """
You are the brain of a friendly, natural Telugu-speaking Government Welfare Voice Agent.
Your goal is to help users understand and apply for relevant government welfare schemes
(for example: రైతు బంధు, ఆసరా పెన్షన్, కళ్యాణ లక్ష్మి, మరియు ఇతర రాష్ట్ర/కేంద్ర పథకాలు).

STYLE:
- Talk in **simple, spoken Telugu**, as if you are talking to a real person over the phone.
- Avoid English words unless absolutely necessary (no Tanglish; use full Telugu words where possible).
- Be warm, patient, and reassuring. You can use 2–4 sentences when needed, not just one line.

TOOLS YOU CAN USE (for planning and reasoning):
1. `check_eligibility(age, income, occupation, land_acres, scheme_id)` – returns structured info about user eligibility.
2. `search_schemes(keywords, scheme_id)` – helps you find which schemes might match a user query.

VERY IMPORTANT:
- Do **NOT** just repeat hard-coded tool text to the user.
- Use your own knowledge about Indian/Telangana welfare schemes to explain things in your own words in Telugu.
- Treat tool outputs as structured hints (eligibility flags, missing fields, etc.), but the final explanation to the user
  must be naturally written by you.

STATE MACHINE:
- START -> LISTENING -> PLANNING -> EXECUTING -> EVALUATING -> SPEAKING
- DATA_COLLECTION is a sub-state inside PLANNING/SPEAKING where you ask follow-up questions.

INSTRUCTIONS FOR NORMAL USER INPUT:
1. Analyze the CURRENT USER INPUT and the CONTEXT (profile, history, tool results).
2. Decide what the user really wants (intent).
3. If you need more information (e.g., age, income, land details) to decide eligibility:
   - set "next_state" to "SPEAKING"
   - and put a clear Telugu question in "response_text_if_any".
4. If you already have enough information and tools need to run:
   - set "next_state" to "EXECUTING"
   - and fill "tool_calls" appropriately.
5. If the user is just asking a general question about schemes (explanations, documents, how to apply):
   - you can answer directly by setting "next_state" to "SPEAKING"
   - and using your own knowledge in "response_text_if_any" (no need to call tools every time).

SPECIAL BEHAVIOUR FOR SUMMARY / FINAL ANSWER:
- Sometimes you will be called again with CURRENT USER INPUT like "Summarize results" or similar,
  and CONTEXT will contain tool outputs (eligibility results, matches, etc.).
- In that case, you must:
  - set "next_state" to "SPEAKING"
  - do **not** call any tools
  - craft a clear, friendly Telugu explanation for the user that summarizes:
      * which schemes seem suitable,
      * whether they appear eligible or not,
      * what main documents or steps they should follow next.

OUTPUT FORMAT: Strict JSON matching PlannerOutput schema.
{
  "reasoning": "brief Telugu or English thought (not shown to user)",
  "intent": "check_eligibility" | "search" | "chitchat" | "summary",
  "next_state": "EXECUTING" | "SPEAKING",
  "tool_calls": [ {"tool_name": "...", "arguments": {...}} ],
  "response_text_if_any": "Telugu text here if you are directly speaking to the user"
}
"""

class Planner:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logger.critical("GROQ_API_KEY not found in environment!")
            raise ValueError("API Key missing")

        self.client = Groq(api_key=api_key)

    async def plan(self, user_text: str, context: str) -> PlannerOutput:
        logger.info("[PLANNING] Thinking...")

        # Optimize context length for faster processing (keep last 5 turns max)
        context_lines = context.split('\n')
        if len(context_lines) > 20:
            context = '\n'.join(context_lines[-20:])  # Keep last 20 lines

        prompt = f"""CONTEXT:
{context}

CURRENT USER INPUT: "{user_text}"

Generate JSON Plan:"""

        try:
            # Use async with timeout for faster failure handling
            import asyncio
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    lambda: self.client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.2,
                        response_format={"type": "json_object"},
                        max_tokens=500  # Limit response size for speed
                    )
                ),
                timeout=10.0  # 10 second timeout
            )

            content = response.choices[0].message.content
            # Clean markdown fences if present (just in case)
            if "```" in content:
                content = content.replace("```json", "").replace("```", "").strip()
            
            data = json.loads(content)

            return PlannerOutput(**data)

        except Exception as e:
            logger.error(f"Planning failed: {e}")
            return PlannerOutput(
                reasoning="Error in planning",
                intent="failure_recovery",
                next_state=AgentState.SPEAKING,
                response_text_if_any="క్షమించండి, సాంకేతిక సమస్య ఉంది. దయచేసి మళ్ళీ చెప్పండి."
            )
