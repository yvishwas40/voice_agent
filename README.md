# Voice Agent System

A robust, voice-first AI agent designed for interactive services, featuring a modern web interface and an intelligent agentic backend.

## 📋 Features

*   **Voice Interface**: Real-time voice interaction using `sounddevice` for capture and `edge-tts` for synthesis.
*   **Speech Recognition**: Powered by `faster-whisper` for low-latency on-device transcription.
*   **Agentic Intelligence**: Implements a Planner-Executor-Evaluator architecture for complex task handling.
*   **Backend**: High-performance FastAPI server with WebSocket support for real-time state streaming.
*   **Frontend**: Interactive web dashboard for monitoring agent state and conversation flow.
*   **LLM Integration**: Uses Groq for ultra-fast inference.

## 🛠️ Prerequisites

*   **Python**: Version 3.10 or higher.
*   **FFmpeg**: Required for audio processing (ensure it's in your system PATH).
*   **API Keys**:
    *   **Groq API Key**: For the LLM backend.

## 🚀 Installation

1.  **Clone the repository** (if you haven't already):
    ```bash
    git clone <repository-url>
    cd "Voice agent"
    ```

2.  **Create a Virtual Environment**:
    It is recommended to use a virtual environment to manage dependencies.
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # Linux/Mac
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## ⚙️ Configuration

1.  Create a `.env` file in the project root directory.
2.  Add your API keys and configuration variables:

    ```env
    # Required for the planner/agent
    GROQ_API_KEY=your_groq_api_key_here
    
    # Optional: If using Google Cloud Speech capabilities
    # GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
    ```

## ▶️ Running the Application

1.  **Start the Server**:
    Run the application module from the project root. This starts the FastAPI backend and enables the WebSocket server.

    ```bash
    python -m voice_agent.app
    ```
    
    *The server will start on `http://localhost:8001`.*

2.  **Access the Dashboard**:
    Open your web browser and navigate to:
    
    [http://localhost:8001](http://localhost:8001)

    Click "Start Conversation" or use the microphone icon to interact with the agent.

## 📂 Project Structure

*   `voice_agent/`: Main application package.
    *   `agent/`: Core agent logic (Planner, Executor, Memory).
    *   `server/`: backend service and state management.
    *   `static/`: Frontend assets (HTML, CSS, JS).
    *   `tools/`: Capability modules for the agent.
*   `requirements.txt`: Python package dependencies.

## 🧪 Troubleshooting

*   **Audio Issues**: Ensure your microphone is set as the default input device in Windows settings.
*   **Missing FFmpeg**: If you encounter errors related to audio processing or `pydub`/`whisper`, verify FFmpeg installation.
*   **API Errors**: specific API errors usually indicate invalid keys in the `.env` file. Check the logs for details.
