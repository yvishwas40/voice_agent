# Voice Agent: Complete Technical Guide & Architecture

## 1. Executive Summary

**Project Name**: Voice Agent for Government Welfare Schemes (Telangana Context)
**Goal**: To provide a natural, voice-first adversarial agent that helps citizens understand and apply for government schemes (like Rythu Bandhu, Asara Pensions) in their native language (Telugu).

This system is not just a chatbot; it is an **agentic AI** that plans, executes tools, evaluates results, and maintains conversation state in real-time. It bridges the gap between complex government databases and rural citizens using a voice interface.

---

## 2. High-Level Architecture

The system follows a **Planner-Executor-Evaluator** architecture, wrapped in a real-time event loop.

### 2.1 The "Brain" (Agentic Loop)
At its core, the agent operates in a continuous cycle:

1.  **Perceive**: Listen to audio, transcribe to text.
2.  **Think**: Analyze context, history, and intent.
3.  **Plan**: Decide on the next action (Speak, Search, Check Eligibility).
4.  **Act**: Execute tools or generate speech.
5.  **Observe**: Evaluate tool outputs.
6.  **Respond**: Synthesize speech back to the user.

### 2.2 System Diagram

```mermaid
graph TD
    User((User)) <-->|Voice/Audio| Frontend[Web Client / Mic]
    Frontend <-->|WebSocket| Backend[FastAPI Server]
    
    subgraph "Agent Service (Backend)"
        State[State Manager]
        STT[Speech-to-Text\n(Faster-Whisper)]
        TTS[Text-to-Speech\n(Edge-TTS)]
        
        Planner[Planner\n(Llama-3 via Groq)]
        Executor[Executor\n(Tool Runner)]
        Evaluator[Evaluator\n(Result Analyzer)]
        Memory[Memory Manager]
    end
    
    Backend --> STT
    STT --> Memory
    Memory --> Planner
    Planner -->|JSON Plan| Executor
    Executor -->|Tool Output| Evaluator
    Evaluator -->|Synthesis| Planner
    Planner -->|Response Text| TTS
    TTS --> Frontend
```

---

## 3. Technical Deep Dive

### 3.1 Technology Stack & Justification

| Component | Technology | Why this choice? |
| :--- | :--- | :--- |
| **Language** | Python 3.10+ | Huge ecosystem for AI/ML and audio processing. |
| **Audio Input** | `sounddevice` | Low-level, cross-platform hardware access. Low latency compared to `pyaudio`. |
| **STT (Ear)** | `faster-whisper` | Runs locally or on edge. Much faster than original OpenAI Whisper. Optimized for CPU/GPU. |
| **LLM (Brain)** | `Groq` (Llama 3.3) | **Speed**. Groq offers LPU (Language Processing Units) that serve tokens at ~300-500 tok/s, crucial for real-time voice. |
| **TTS (Mouth)** | `edge-tts` | Free, high-quality neural voices from Microsoft Edge. Better than standard Python `pyttsx3`. |
| **Backend** | `FastAPI` + `WebSockets` | Asynchronous speed. Use WebSockets to stream state (transcripts, thoughts) to UI in real-time. |

### 3.2 The State Machine
The agent functionality is governed by a strict state machine to prevent race conditions (e.g., listening while speaking).

*   **IDLE**: Waiting for trigger.
*   **LISTENING**: Microphone active, buffering audio frames.
*   **THINKING**: Transcribing audio -> sending context to LLM.
*   **PLANNING**: LLM generating structured JSON.
*   **EXECUTING**: Running Python code (DB lookups, API calls).
*   **SPEAKING**: Streaming audio output to speakers.

**Key Code Reference**: `voice_agent/server/agent_service.py` manages these transitions.

---

## 4. Methodologies & Implementation Details

### 4.1 The Planning Engine (`Planner`)
Located in `agent/planner.py`.
*   **Input**: User text + Conversation History (Context).
*   **Mechanism**: A prompt engineered LLM call.
*   **Output**: Strict JSON.
    *   `intent`: What the user wants.
    *   `tool_calls`: List of functions to run.
    *   `response_text`: If no tools are needed (chitchat).

**Why JSON?**
It makes the output deterministic. We can parse it programmatically. If the LLM just "chatted", we couldn't easily trigger database queries.

### 4.2 Memory Management
Located in `agent/memory.py`.
*   **Short-term**: Rolling window of last ~5-10 turns.
*   **Profile Memory**: Extracts and persists specific entities (e.g., User Income: 50k, Land: 2 acres).
*   **Conflict Detection**: If a user says "I have 5 acres" then later "I have no land", the system detects this inconsistency.

### 4.3 Evaluation
Located in `agent/evaluator.py`.
After tools run, raw data (e.g., `{"eligible": true, "amount": 5000}`) assumes the user understands JSON. The **Evaluator** looks at this raw data and decides:
1.  Is this enough to answer? -> **Synthesize** a natural language response.
2.  Did it fail? -> **Ask User** for clarification.

---

## 5. Interview Q&A Guide

**Q: Can you explain the flow of a single user request?**
**A:**
1.  **Capture**: User audio is captured via `sounddevice` into a numpy array.
2.  **Transcribe**: `faster-whisper` converts audio to text "Am I eligible?".
3.  **Context Construction**: We fetch the last few messages from `MemoryManager`.
4.  **Planning**: `Planner` sends this to Groq with a system prompt defining available tools.
5.  **Decision**: LLM returns JSON `{"intent": "check_eligibility", "tool_calls": [...]}`.
6.  **Execution**: `Executor` runs the Python function `check_eligibility()`.
7.  **Synthesis**: The result is fed back to the LLM to generate a natural Telugu sentence.
8.  **Output**: `edge-tts` converts the sentence to audio, played back to the user.

**Q: How do you handle latency?**
**A:**
*   We use **Groq** for near-instant inference.
*   We use **faster-whisper** (optimized CTranslate2 backend) instead of vanilla Whisper.
*   We stream state updates via WebSockets so the user sees "Thinking..." feedback immediately.

**Q: How do you ensure the LLM follows instructions?**
**A:**
*   **System Prompting**: We strongly enforce a persona ("You are a government official... speak Telugu").
*   **JSON Mode**: We force the LLM to output valid JSON, preventing it from rambling.
*   **Error Recovery**: If the LLM outputs garbage, the `try/except` block in `Planner` catches it and returns a polite fallback message.

**Q: How is this "Agentic"?**
**A:** it's not just a fancy search engine. It has **agency**:
*   It can **ask follow-up questions** if data is missing (e.g., "I need your income first").
*   It **evaluates** its own work (using the Evaluator component).
*   It maintains **state** across multiple turns.

---

## 6. Directory Structure (Mental Map)

*   `voice_agent/`
    *   `agent/`: The brain.
        *   `planner.py`: Decision making.
        *   `executor.py`: Tool runner.
        *   `memory.py`: Context storage.
    *   `server/`: The body.
        *   `agent_service.py`: Main loop.
        *   `state_manager.py`: WebSocket/UI sync.
    *   `tools/`: The hands.
        *   `eligibility.py`: Logic for scheme rules.
