# ORCHIX v1.1
'''Success message hook for LightRAG'''


def get_success_message(config: dict) -> str:
    '''Get success message after installation'''
    port = config.get('port', 8000)
    llm_provider = config.get('llm_provider', 'openai')
    llm_model = config.get('llm_model', 'gpt-4')
    embed_provider = config.get('embed_provider', 'openai')
    embed_model = config.get('embed_model', 'text-embedding-3-small')

    message = f"""💡 LightRAG Development Container installed successfully!

Container Access:
  Port: {port}
  Shell: docker exec -it lightrag bash
  Python: docker exec -it lightrag python

Configuration:
  LLM Provider: {llm_provider}
  LLM Model: {llm_model}
  Embedding Provider: {embed_provider}
  Embedding Model: {embed_model}

Installed Packages:
  ✓ OpenAI SDK (for LLM calls)
  ✓ FastAPI (for building APIs)
  ✓ Uvicorn (web server)
  ✓ Pydantic (data validation)

Next Steps:
  1. Access the container: docker exec -it lightrag bash
  2. Install additional packages: pip install <package>
  3. Create your RAG application in /app
  4. Store data in /app/data (persisted volume)

Example RAG Application:
  # Create app.py in /app
  from openai import OpenAI

  client = OpenAI(api_key="your-key")
  response = client.chat.completions.create(
      model="{llm_model}",
      messages=[{{"role": "user", "content": "Hello"}}]
  )
"""

    return message
