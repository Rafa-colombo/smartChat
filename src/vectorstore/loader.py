import os
import chromadb
from chromadb.config import Settings

def inicializar_e_popular_rag():
    """
    Inicializa o ChromaDB com persistência em disco e preenche 
    regras padrão e de teste para o sistema de RAG do chatbot.
    """
    persist_directory = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")
    
    print(f"[VectorStore] Inicializando banco vetorial em: {persist_directory}")
    
    # Configura o cliente persistente do ChromaDB
    client = chromadb.PersistentClient(path=persist_directory)
    
    # Cria a collection de regras e contexto
    collection_name = "chatbot_knowledge_base"
    
    # Se a collection já existir, resetar ou apenas adicionar dados de teste
    try:
        collection = client.get_or_create_collection(name=collection_name)
    except Exception as e:
        print(f"[VectorStore] Erro ao criar collection: {e}")
        raise e

    # Regras padrão e de teste para injetar no RAG
    regras_rag = [
        {
            "id": "regra_01",
            "document": "Regra padrão de atendimento: O assistente deve ser sempre educado, claro, objetivo e utilizar formatação em Markdown para estruturar as respostas.",
            "metadata": {"categoria": "padrao", "tipo": "diretriz"}
        },
        {
            "id": "regra_02",
            "document": "Política de consulta de CEP: Sempre que o usuário fornecer um CEP com 8 dígitos, utilize a ferramenta consultar_cep para buscar logradouro, bairro, localidade e UF.",
            "metadata": {"categoria": "padrao", "tipo": "ferramenta_viacep"}
        },
        {
            "id": "regra_03",
            "document": "Política de consulta de Pokémon: Sempre que o usuário mencionar o nome ou ID de um pokémon, utilize a ferramenta consultar_pokemon para retornar dados como altura, peso e tipos.",
            "metadata": {"categoria": "padrao", "tipo": "ferramenta_pokeapi"}
        },
        {
            "id": "regra_04",
            "document": "Cenário de Teste - Resiliência: Se uma API externa (como ViaCEP ou PokéAPI) falhar ou retornar erro 500, a ferramenta deve tratar a exceção e retornar um dicionário contendo a chave 'erro'.",
            "metadata": {"categoria": "teste", "tipo": "resiliencia"}
        },
        {
            "id": "regra_05",
            "document": "Cenário de Teste - Feedback Dinâmico: O sistema permite avaliar respostas com notas de 1 a 5 e sugestões, reescrevendo o prompt do sistema dinamicamente através do agente.",
            "metadata": {"categoria": "teste", "tipo": "feedback"}
        }
    ]

    # Extrai os dados para inserção em lote no ChromaDB
    ids = [r["id"] for r in regras_rag]
    documents = [r["document"] for r in regras_rag]
    metadatas = [r["metadata"] for r in regras_rag]

    # Adiciona ou atualiza os dados na collection
    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )
    
    print(f"[VectorStore] Sucesso! {len(regras_rag)} regras de RAG injetadas e salvas no disco.")
    return client

if __name__ == "__main__":
    inicializar_e_popular_rag()