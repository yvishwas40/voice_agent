from .schemas import PlannerOutput, AgentState, EvaluatorOutput
from ..tools.definitions import ToolOutput
from ..utils.logger import logger
import json

class Evaluator:
    def evaluate(self, 
                 plan: PlannerOutput, 
                 tool_results: list[ToolOutput], 
                 memory_context: str) -> EvaluatorOutput:
        
        logger.info("[EVALUATING] Analyzing results...")
        
        # 1. Check for Failures
        failed_tools = [res for res in tool_results if not res.success]
        if failed_tools:
            return EvaluatorOutput(
                action="RETRY_OR_FAIL",
                reason=f"టూల్ నడిపే సమయంలో లోపం వచ్చింది: {[f.error for f in failed_tools]}"
            )

        # 2. Check for Missing Info (Specific to Eligibility Tool)
        for res in tool_results:
            if res.data and res.data.get("status") == "MISSING_INFO":
                return EvaluatorOutput(
                    action="ASK_USER",
                    reason="అవసరమైన వివరాలు పూర్తి లేవు",
                    clean_response=(
                        "మీరు ఏ పథకానికి అర్హులా అనేది ఖచ్చితంగా చెప్పాలంటే "
                        f"మరిన్ని వివరాలు కావాలి. దయచేసి ఇవి చెప్పండి: {', '.join(res.data.get('missing_fields', []))}."
                    )
                )

        # 3. Success -> Prepare for Speech
        # Since we use LLM for synthesis, here we just flag success
        # In a real system, Evaluator might ping LLM again to synthesize the answer
        # For now, we assume Planner Loop will handle the synthesis in the next prompt,
        # OR we construct a simple string here.
        
        # Let's aggregate data for synthesis
        data_summary = json.dumps([r.data for r in tool_results], ensure_ascii=False)
        return EvaluatorOutput(
            action="SYNTHESIZE", 
            reason="టూల్ అమలు విజయవంతంగా పూర్తైంది",
            clean_response=data_summary # Passed back to LLM context
        )
