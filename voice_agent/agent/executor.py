from ..tools.eligibility import EligibilityEngine, EligibilityInput
from ..tools.knowledge import SchemeKnowledgeRetriever, SchemeLookupInput
from ..tools.definitions import ToolOutput
from .schemas import PlanStep
from ..utils.logger import logger

class Executor:
    def __init__(self):
        self.eligibility_engine = EligibilityEngine()
        self.knowledge_retriever = SchemeKnowledgeRetriever()

    async def execute(self, tool_call: PlanStep) -> ToolOutput:
        logger.info(f"[EXECUTING] {tool_call.tool_name} with {tool_call.arguments}")
        
        name = tool_call.tool_name.lower()
        args = tool_call.arguments
        
        try:
            if name == "check_eligibility":
                # Clean args mapping
                input_data = EligibilityInput(**args)
                scheme_id = args.get("scheme_id")
                return self.eligibility_engine.check(input_data, scheme_id)

            elif name == "search_schemes":
                input_data = SchemeLookupInput(**args)
                return self.knowledge_retriever.search(input_data)
            
            else:
                return ToolOutput(success=False, error=f"Unknown Tool: {name}")

        except Exception as e:
            logger.error(f"Execution Error: {e}")
            return ToolOutput(success=False, error=str(e))
