import google.generativeai as genai
import importlib
import os

# Import chromadb
try:
    chromadb = importlib.import_module("chromadb")
except ModuleNotFoundError:
    raise ModuleNotFoundError("ChromaDB module isn't imported, I refuse to continue!")

class GeminiDocumentRetrieval(chromadb.EmbeddingFunction):
    def __call__(self, input: chromadb.Documents) -> chromadb.Embeddings: # type: ignore
        model = 'models/text-embedding-004'
        title = "Web Search Query"
        genai.configure(api_key=os.environ.get("GOOGLE_AI_TOKEN"))

        return genai.embed_content(model=model,
                                    content=input,
                                    task_type="retrieval_document",
                                    title=title)["embedding"]
