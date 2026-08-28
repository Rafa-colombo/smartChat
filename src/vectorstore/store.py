import chromadb
from chromadb.config import Settings
import os
# RAG
class VectorStoreManager:
    def __init__(self, collection_name: str = "chatbot_knowledge"):
        # Cria um cliente do Chroma persistente na pasta /data/chroma_db do projeto
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/chroma_db"))
        
        self.client = chromadb.PersistentClient(path=db_path)
        
        # Cria ou obtém a collection (tabela vetorial)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def adicionar_documento(self, doc_id: str, texto: str, metadata: dict = None):
        """Adiciona um texto/documento à base vetorial de forma segura."""
        kwargs = {
            "documents": [texto],
            "ids": [doc_id]
        }
        if metadata:
            kwargs["metadatas"] = [metadata]
            
        self.collection.add(**kwargs)

    def buscar_contexto(self, query: str, n_results: int = 2) -> list:
        """Busca os trechos mais relevantes na base vetorial com base na pergunta do usuário."""
        if self.collection.count() == 0:
            return []
            
        resultados = self.collection.query(
            query_texts=[query],
            n_results=min(n_results, self.collection.count())
        )
        
        # Retorna apenas a lista de textos encontrados
        return resultados.get("documents", [[]])[0]