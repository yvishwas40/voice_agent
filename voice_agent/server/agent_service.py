import asyncio
from ..utils.voice_io import VoiceInterface
from ..agent.planner import Planner
from ..agent.executor import Executor
from ..agent.evaluator import Evaluator
from ..agent.memory import MemoryManager
from ..agent.schemas import AgentState
from .state_manager import StateManager
from ..utils.logger import logger

class AgentService:
    def __init__(self):
        self.running = False
        self.state_manager = StateManager()

    async def start(self):
        if self.running:
            return
        self.running = True
        asyncio.create_task(self._run_loop())

    async def stop(self):
        self.running = False

    async def _run_loop(self):
        logger.info("Agent Service Started")
        
        try:
            voice = VoiceInterface()
            planner = Planner()
            executor = Executor()
            evaluator = Evaluator()
            memory = MemoryManager()
            
            # Initial Greeting
            await self.state_manager.set_status("SPEAKING")
            greeting = "నమస్కారం! నేను తెలంగాణ ప్రభుత్వ సంక్షేమ పథకాల సహాయకుడు. మీకు ఏ పథకం గురించి తెలుసుకోవాలి లేదా ఏ దరఖాస్తుకు సహాయం కావాలి? మైక్ బటన్‌పై నొక్కి తెలుగులో మాట్లాడండి లేదా సందేశాన్ని టైప్ చేయండి."
            await self.state_manager.add_transcript("agent", greeting)
            await voice.speak(greeting)
            await self.state_manager.set_status("IDLE")

            while self.running:
                try:
                    # 0. Check if there is any typed text from UI (fallback)
                    typed_text = await self.state_manager.consume_text_input()
                    if typed_text:
                        user_text = typed_text
                        is_text = True
                    else:
                        is_text = False

                    # If no typed text, respect UI start/stop listening control
                    if not is_text:
                        if not self.state_manager.listening_active:
                            # print("waiting for listening_active")
                            await asyncio.sleep(0.1)
                            continue

                        # 1. LISTEN (continuous loop while listening_active is True)
                        # Only set status if we weren't just listening to avoid flicker
                        if self.state_manager.status != "LISTENING":
                             await self.state_manager.set_status("LISTENING")
                        
                        # Use Whisper with quality metadata
                        user_text, quality = await asyncio.to_thread(voice.listen_with_quality)

                        if not user_text:
                            # No valid Telugu speech detected, go back to idle and continue loop
                            # await self.state_manager.set_status("IDLE") # Don't just go idle, keep listening
                            await asyncio.sleep(0.1)
                            continue

                        # Only confirm if quality is low (optional confirmation for better UX)
                        # Skip confirmation for high-quality transcriptions to speed up interaction
                        if quality and quality < 0.7:  # Low confidence threshold
                            confirm_prompt = (
                                f"మీరు ఇలా అన్నారా: \"{user_text}\"? "
                                "సరి అయితే 'అవును' అని, కాకపోతే 'కాదు' అని చెప్పండి."
                            )
                            await self.state_manager.set_status("SPEAKING")
                            await self.state_manager.add_transcript("agent", confirm_prompt)
                            await voice.speak(confirm_prompt)

                            # Listen briefly for confirmation
                            await self.state_manager.set_status("LISTENING")
                            confirm_text, _ = await asyncio.to_thread(voice.listen_with_quality)

                            if not confirm_text or ("అవును" not in confirm_text and "yes" not in confirm_text.lower()):
                                # Ask user to either repeat or use text input
                                retry_msg = (
                                    "సరే, మీ మాట పూర్తిగా స్పష్టంగా రాలేదు. "
                                    "దయచేసి మెల్లిగా మళ్లీ చెప్పండి లేదా క్రింద ఉన్న బాక్స్‌లో టైప్ చేయండి."
                                )
                                await self.state_manager.set_status("SPEAKING")
                                await self.state_manager.add_transcript("agent", retry_msg)
                                await voice.speak(retry_msg)
                                await self.state_manager.set_status("IDLE")
                                await asyncio.sleep(0.1)
                                continue
                        # High quality or typed text - proceed directly without confirmation

                    # Log user text for both voice and typed input
                    await self.state_manager.add_transcript("user", user_text)
                    await self.state_manager.set_status("THINKING")

                    # Update Memory
                    memory.add_turn("user", user_text)

                    # 2. PLAN
                    context = memory.get_context_block()
                    await self.state_manager.add_thought(f"Planning for: {user_text}")
                    plan = await planner.plan(user_text, context)
                    await self.state_manager.add_thought(f"Intent: {plan.intent}")

                    # 3. ACT
                    if plan.next_state == AgentState.SPEAKING:
                        response = plan.response_text_if_any or "..."
                        await self.state_manager.set_status("SPEAKING")
                        # Show transcript immediately for instant user feedback
                        await self.state_manager.add_transcript("agent", response)
                        # Voice plays after transcript is shown (non-blocking for UI, but sequential for audio)
                        await voice.speak(response)
                        memory.add_turn("agent", response)
                    
                    elif plan.next_state == AgentState.EXECUTING:
                        tool_results = []
                        for step in plan.tool_calls:
                            await self.state_manager.add_thought(f"Executing: {step.tool_name}")
                            result = await executor.execute(step)
                            tool_results.append(result)
                            await self.state_manager.add_thought(f"Result: {result.success}")
                        
                        evaluation = evaluator.evaluate(plan, tool_results, context)
                        
                        if evaluation.action == "SYNTHESIZE":
                            # Quick Synthesis - use evaluator's clean_response if available, otherwise synthesize
                            await self.state_manager.add_thought(f"Synthesizing response...")
                            
                            # If evaluator already provided a good response, use it directly
                            if evaluation.clean_response and len(evaluation.clean_response.strip()) > 20:
                                final_resp = evaluation.clean_response
                            else:
                                # Otherwise, synthesize with planner
                                result_context = f"User asked: {user_text}. Tool results: {evaluation.clean_response}"
                                final_plan = await planner.plan("Summarize results in simple Telugu", result_context)
                                final_resp = final_plan.response_text_if_any or evaluation.clean_response or "సమాచారం సిద్ధంగా ఉంది."
                            
                            await self.state_manager.set_status("SPEAKING")
                            # Show transcript immediately for instant user feedback
                            await self.state_manager.add_transcript("agent", final_resp)
                            await voice.speak(final_resp)
                            memory.add_turn("agent", final_resp)

                        elif evaluation.action == "ASK_USER":
                             await self.state_manager.set_status("SPEAKING")
                             # Show transcript immediately for instant user feedback
                             await self.state_manager.add_transcript("agent", evaluation.clean_response)
                             await voice.speak(evaluation.clean_response)
                             memory.add_turn("agent", evaluation.clean_response)
                    
                    await self.state_manager.set_status("IDLE")
                    # Reduced sleep for faster response cycle
                    await asyncio.sleep(0.05)

                except Exception as e:
                    logger.error(f"Error in Agent Loop Iteration: {e}")
                    await self.state_manager.add_thought(f"ERROR: {e} - Recovering...")
                    await self.state_manager.set_status("IDLE")
                    await asyncio.sleep(1) # Sleep a bit to avoid rapid error loops but keep running

        except Exception as e:
            # Outer crash (should happen rarely now)
            logger.critical(f"Agent Service CRASHED: {e}")
            await self.state_manager.add_thought(f"CRITICAL SYSTEM FAILURE: {e}")
            self.running = False
