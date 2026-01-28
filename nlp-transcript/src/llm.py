from langchain_ollama import OllamaLLM

llm = OllamaLLM(
    model="phi3:mini",
    temperature=0
)
