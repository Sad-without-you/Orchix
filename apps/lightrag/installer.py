from apps.installer_base import BaseInstaller
import subprocess
import os
from cli.ui import show_step_detail, show_step_line, step_input, step_select
from utils.docker_progress import run_docker_with_progress, filter_docker_errors


class LightRAGInstaller(BaseInstaller):
    '''Installer for LightRAG framework'''

    def check_dependencies(self):
        '''Check if Docker is available'''
        try:
            result = subprocess.run(
                ['docker', '--version'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def get_configuration(self, instance_name=None):
        '''Get LightRAG configuration from user'''

        show_step_detail("Configure LightRAG framework")
        show_step_line()

        config = {}

        # Port (set later in install_menu.py)
        config['port'] = self.manifest['default_ports'][0]

        # LLM Provider
        llm_choice = step_select(
            "LLM Provider",
            [
                "🤖 OpenAI",
                "🧠 Anthropic (Claude)",
                "🦙 Ollama (Local)",
                "⚙️  Custom API"
            ]
        )

        if "OpenAI" in llm_choice:
            config['llm_provider'] = 'openai'
            config['llm_api_key'] = step_input("OpenAI API Key: ").strip()

            # OpenAI Model Selection with Details
            model_choice = step_select(
                "OpenAI Model",
                [
                    "GPT-4o (128K tokens, Latest flagship, Recommended)",
                    "GPT-4o-mini (128K tokens, Fast & affordable)",
                    "o3-mini (200K tokens, Fast reasoning, Great value)",
                    "o1 (200K tokens, Advanced reasoning, Expensive)"
                ]
            )

            if "GPT-4o-mini" in model_choice:
                config['llm_model'] = "gpt-4o-mini"
            elif "GPT-4o" in model_choice:
                config['llm_model'] = "gpt-4o"
            elif "o3-mini" in model_choice:
                config['llm_model'] = "o3-mini"
            elif "o1" in model_choice:
                config['llm_model'] = "o1"
            else:
                config['llm_model'] = "gpt-4o"

        elif "Anthropic" in llm_choice:
            config['llm_provider'] = 'anthropic'
            config['llm_api_key'] = step_input("Anthropic API Key: ").strip()

            # Anthropic Model Selection with Details
            model_choice = step_select(
                "Anthropic Model",
                [
                    "Claude Sonnet 4.5 (200K tokens, Best balance, Recommended)",
                    "Claude Opus 4.6 (200K tokens, Most capable, Expensive)",
                    "Claude Haiku 4.5 (200K tokens, Fast & affordable)",
                    "Claude 3.5 Sonnet (200K tokens, Reliable, Legacy)"
                ]
            )

            if "Opus 4.6" in model_choice:
                config['llm_model'] = "claude-opus-4-6"
            elif "Sonnet 4.5" in model_choice:
                config['llm_model'] = "claude-sonnet-4-5-20250929"
            elif "Haiku 4.5" in model_choice:
                config['llm_model'] = "claude-haiku-4-5-20251001"
            else:
                config['llm_model'] = "claude-3-5-sonnet-20241022"

        elif "Ollama" in llm_choice:
            config['llm_provider'] = 'ollama'
            config['llm_base_url'] = step_input("Ollama URL (default: http://localhost:11434): ").strip() or "http://localhost:11434"

            # Ollama Model Selection with Details
            model_choice = step_select(
                "Ollama Model",
                [
                    "Llama 3.1 70B (128K tokens, Best quality, Needs 40GB+ RAM)",
                    "Llama 3.1 8B (128K tokens, Fast, Needs 8GB RAM)",
                    "Mistral 7B (32K tokens, Very fast, Needs 4GB RAM)",
                    "Mixtral 8x7B (32K tokens, High quality, Needs 24GB RAM)",
                    "Phi-3 Mini (4K tokens, Ultra fast, Needs 2GB RAM)",
                    "Custom Model"
                ]
            )

            if "Llama 3.1 70B" in model_choice:
                config['llm_model'] = "llama3.1:70b"
            elif "Llama 3.1 8B" in model_choice:
                config['llm_model'] = "llama3.1:8b"
            elif "Mistral 7B" in model_choice:
                config['llm_model'] = "mistral:7b"
            elif "Mixtral" in model_choice:
                config['llm_model'] = "mixtral:8x7b"
            elif "Phi-3" in model_choice:
                config['llm_model'] = "phi3:mini"
            else:
                config['llm_model'] = step_input("Enter Ollama model name: ").strip()

        else:
            config['llm_provider'] = 'custom'
            config['llm_base_url'] = step_input("API Base URL: ").strip()
            config['llm_api_key'] = step_input("API Key (if needed): ").strip()
            config['llm_model'] = step_input("Model name: ").strip()

        # Embedding Provider
        embed_choice = step_select(
            "Embedding Provider",
            [
                "🤖 OpenAI",
                "🦙 Ollama (Local)",
                "⚙️  Same as LLM Provider"
            ]
        )

        if "Same as LLM" in embed_choice:
            config['embed_provider'] = config['llm_provider']
            config['embed_model'] = 'default'
        elif "OpenAI" in embed_choice:
            config['embed_provider'] = 'openai'
            config['embed_api_key'] = step_input("OpenAI API Key (or use LLM key): ").strip() or config.get('llm_api_key', '')

            # OpenAI Embedding Model Selection
            embed_model_choice = step_select(
                "OpenAI Embedding Model",
                [
                    "text-embedding-3-large (3072 dim, Best quality, More expensive)",
                    "text-embedding-3-small (1536 dim, Good quality, Recommended)",
                    "text-embedding-ada-002 (1536 dim, Legacy, Cheapest)"
                ]
            )

            if "3-large" in embed_model_choice:
                config['embed_model'] = "text-embedding-3-large"
            elif "3-small" in embed_model_choice:
                config['embed_model'] = "text-embedding-3-small"
            else:
                config['embed_model'] = "text-embedding-ada-002"

        else:
            config['embed_provider'] = 'ollama'
            config['embed_base_url'] = step_input("Ollama URL (default: http://localhost:11434): ").strip() or "http://localhost:11434"

            # Ollama Embedding Model Selection
            embed_model_choice = step_select(
                "Ollama Embedding Model",
                [
                    "nomic-embed-text (768 dim, Best quality, Recommended)",
                    "mxbai-embed-large (1024 dim, High quality, Larger)",
                    "all-minilm (384 dim, Fast, Lightweight)"
                ]
            )

            if "nomic" in embed_model_choice:
                config['embed_model'] = "nomic-embed-text"
            elif "mxbai" in embed_model_choice:
                config['embed_model'] = "mxbai-embed-large"
            else:
                config['embed_model'] = "all-minilm"

        show_step_line()
        show_step_detail("Configuration complete!")

        return config

    def install(self, config, instance_name=None):
        '''Install LightRAG using Docker Compose'''

        instance_name = config.get('instance_name', 'lightrag')
        compose_file = f"docker-compose-{instance_name}.yml"
        dockerfile_path = f"Dockerfile-{instance_name}"

        try:
            # Generate Dockerfile
            dockerfile_content = self._generate_dockerfile(config)
            with open(dockerfile_path, 'w') as f:
                f.write(dockerfile_content)

            # Generate compose file
            compose_content = self._generate_compose(config, dockerfile_path)
            with open(compose_file, 'w') as f:
                f.write(compose_content)

            # Build image
            result = run_docker_with_progress(
                ['docker', 'build', '-t', f'{instance_name}:latest', '-f', dockerfile_path, '.'],
                f"Building {instance_name} image"
            )

            if result.returncode != 0:
                show_step_detail(f"Build failed: {result.stderr}")
                self._cleanup([compose_file, dockerfile_path])
                return False

            # Run docker compose
            result = run_docker_with_progress(
                ['docker', 'compose', '-f', compose_file, 'up', '-d'],
                f"Starting {instance_name} container"
            )

            if result.returncode != 0:
                # Filter out Docker pull progress, show only actual errors
                error_output = filter_docker_errors(result.stderr)
                if error_output:
                    show_step_detail(f"Docker error: {error_output}")

                self._cleanup([compose_file, dockerfile_path])
                return False

            return True

        except Exception as e:
            show_step_detail(f"Installation failed: {e}")
            self._cleanup([compose_file, dockerfile_path])
            return False

    def _cleanup(self, files):
        '''Clean up generated files'''
        for filepath in files:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    show_step_detail(f"Cleaned up {filepath}")
            except Exception as e:
                show_step_detail(f"Could not cleanup {filepath}: {e}")

    def _generate_dockerfile(self, config):
        '''Generate Dockerfile content'''

        # Get LLM config for demo app
        llm_provider = config.get('llm_provider', 'openai')
        llm_model = config.get('llm_model', 'gpt-4o-mini')

        # Create Python code for main.py
        python_code = f'''from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os

app = FastAPI(title="LightRAG API", version="1.0.0")

class ChatRequest(BaseModel):
    message: str
    model: str = "{llm_model}"

@app.get("/", response_class=HTMLResponse)
async def root():
    with open("/app/static/index.html", "r") as f:
        return f.read()

@app.get("/api/info")
async def info():
    return {{
        "status": "running",
        "provider": "{llm_provider}",
        "model": "{llm_model}"
    }}

@app.get("/health")
async def health():
    return {{"status": "healthy"}}

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        from openai import OpenAI
        api_key = os.getenv("LLM_API_KEY")
        if not api_key:
            return {{"error": "LLM_API_KEY not set"}}

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=request.model,
            messages=[{{"role": "user", "content": request.message}}]
        )
        return {{"response": response.choices[0].message.content}}
    except Exception as e:
        return {{"error": str(e)}}
'''

        # Create HTML UI
        html_code = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LightRAG Chat</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .header p {{ opacity: 0.9; }}
        .status {{ background: white; padding: 15px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .status-item {{ display: inline-block; margin-right: 20px; }}
        .status-label {{ font-weight: bold; color: #667eea; }}
        .chat-box {{ background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; min-height: 400px; max-height: 500px; overflow-y: auto; }}
        .message {{ margin-bottom: 15px; padding: 12px; border-radius: 8px; }}
        .user-message {{ background: #667eea; color: white; margin-left: 50px; }}
        .bot-message {{ background: #f0f0f0; margin-right: 50px; }}
        .input-area {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .input-group {{ display: flex; gap: 10px; }}
        input[type="text"] {{ flex: 1; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; }}
        input[type="text"]:focus {{ outline: none; border-color: #667eea; }}
        button {{ padding: 12px 24px; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; }}
        button:hover {{ background: #5568d3; }}
        button:disabled {{ background: #ccc; cursor: not-allowed; }}
        .error {{ color: #e53e3e; padding: 10px; background: #fff5f5; border-radius: 8px; margin-bottom: 10px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💡 LightRAG Chat</h1>
            <p>Chat with your AI assistant</p>
        </div>

        <div class="status">
            <div class="status-item"><span class="status-label">Provider:</span> <span id="provider">{llm_provider}</span></div>
            <div class="status-item"><span class="status-label">Model:</span> <span id="model">{llm_model}</span></div>
            <div class="status-item"><span class="status-label">Status:</span> <span id="status">🟢 Online</span></div>
        </div>

        <div id="error" class="error" style="display: none;"></div>

        <div class="chat-box" id="chatBox">
            <div class="message bot-message">Hi! I'm your AI assistant. How can I help you today?</div>
        </div>

        <div class="input-area">
            <div class="input-group">
                <input type="text" id="messageInput" placeholder="Type your message..." onkeypress="handleKeyPress(event)">
                <button onclick="sendMessage()" id="sendBtn">Send</button>
            </div>
        </div>
    </div>

    <script>
        async function sendMessage() {{
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            if (!message) return;

            const chatBox = document.getElementById('chatBox');
            const sendBtn = document.getElementById('sendBtn');
            const errorDiv = document.getElementById('error');

            errorDiv.style.display = 'none';

            chatBox.innerHTML += `<div class="message user-message">${{message}}</div>`;
            input.value = '';
            input.disabled = true;
            sendBtn.disabled = true;

            chatBox.scrollTop = chatBox.scrollHeight;

            try {{
                const response = await fetch('/chat', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ message: message, model: "{llm_model}" }})
                }});

                const data = await response.json();

                if (data.error) {{
                    errorDiv.textContent = 'Error: ' + data.error;
                    errorDiv.style.display = 'block';
                    chatBox.innerHTML += `<div class="message bot-message">⚠️ ${{data.error}}</div>`;
                }} else {{
                    chatBox.innerHTML += `<div class="message bot-message">${{data.response}}</div>`;
                }}
            }} catch (error) {{
                errorDiv.textContent = 'Connection error: ' + error.message;
                errorDiv.style.display = 'block';
                chatBox.innerHTML += `<div class="message bot-message">⚠️ Connection error</div>`;
            }}

            input.disabled = false;
            sendBtn.disabled = false;
            input.focus();
            chatBox.scrollTop = chatBox.scrollHeight;
        }}

        function handleKeyPress(event) {{
            if (event.key === 'Enter') {{
                sendMessage();
            }}
        }}

        document.getElementById('messageInput').focus();
    </script>
</body>
</html>
'''

        dockerfile_lines = [
            "FROM python:3.11-slim",
            "",
            "WORKDIR /app",
            "",
            "# Upgrade pip and install build tools",
            "RUN pip install --no-cache-dir --upgrade pip setuptools wheel",
            "",
            "# Install core dependencies",
            "RUN pip install --no-cache-dir \\",
            "    openai==1.35.0 \\",
            "    fastapi==0.111.0 \\",
            "    uvicorn==0.30.0 \\",
            "    httpx==0.27.0 \\",
            "    pydantic==2.7.4 \\",
            "    python-dotenv==1.0.1 \\",
            "    aiofiles==23.2.1",
            "",
            "# Create directories",
            "RUN mkdir -p /app/data /app/static",
            "",
            "# Create FastAPI app",
            "RUN cat > /app/main.py << 'EOFPYTHON'",
            python_code,
            "EOFPYTHON",
            "",
            "# Create HTML UI",
            "RUN cat > /app/static/index.html << 'EOFHTML'",
            html_code,
            "EOFHTML",
            "",
            "# Set environment variables",
            "ENV PYTHONUNBUFFERED=1",
            "ENV PYTHONDONTWRITEBYTECODE=1",
            "",
            "# Expose port",
            "EXPOSE 8000",
            "",
            "# Start FastAPI server",
            'CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]'
        ]

        return '\n'.join(dockerfile_lines)

    def _generate_compose(self, config, dockerfile_path):
        '''Generate docker-compose.yml content'''

        instance_name = config.get('instance_name', 'lightrag')
        volume_name = config.get('volume_name', 'lightrag_data')

        compose_lines = [
            "services:",
            f"  {instance_name}:",
            f"    image: {instance_name}:latest",
            f"    container_name: {instance_name}",
            "    restart: unless-stopped",
            "    ports:",
            f"      - {config['port']}:8000",
            "    environment:"
        ]

        # Add LLM config
        compose_lines.append(f"      - LLM_PROVIDER={config.get('llm_provider', 'openai')}")
        if config.get('llm_api_key'):
            compose_lines.append(f"      - LLM_API_KEY={config['llm_api_key']}")
        if config.get('llm_base_url'):
            compose_lines.append(f"      - LLM_BASE_URL={config['llm_base_url']}")
        compose_lines.append(f"      - LLM_MODEL={config.get('llm_model', 'gpt-4')}")

        # Add Embedding config
        compose_lines.append(f"      - EMBED_PROVIDER={config.get('embed_provider', 'openai')}")
        if config.get('embed_api_key'):
            compose_lines.append(f"      - EMBED_API_KEY={config['embed_api_key']}")
        if config.get('embed_base_url'):
            compose_lines.append(f"      - EMBED_BASE_URL={config['embed_base_url']}")
        compose_lines.append(f"      - EMBED_MODEL={config.get('embed_model', 'text-embedding-3-small')}")

        # Volumes
        compose_lines.extend([
            "    volumes:",
            f"      - {volume_name}:/app/data",
            "",
            "volumes:",
            f"  {volume_name}:",
            f"    name: {volume_name}"
        ])

        return '\n'.join(compose_lines)
