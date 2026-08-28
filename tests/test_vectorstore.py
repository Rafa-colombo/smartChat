from src.vectorstore.store import VectorStoreManager # classe

def test_vectorstore_insercao_e_busca():
    store = VectorStoreManager(collection_name="teste_collection")
    
    # Adiciona um documento de exemplo
    store.adicionar_documento(
        doc_id="msg_abc", 
        texto="A política de reembolso da empresa permite devoluções em até 7 dias úteis.",
        metadata={"categoria": "financeiro"}
    )
    
    # Faz uma busca por similaridade
    contexto = store.buscar_contexto("Como funciona a devolução de dinheiro?")
    
    assert len(contexto) > 0
    assert "reembolso" in contexto[0]

def test_vectorstore_busca_base_vazia():
    """
    Scenario: Buscar contexto em uma base que não possui documentos retorna uma lista vazia sem quebrar.
    """
    store = VectorStoreManager(collection_name="collection_vazia_teste")
    # Força a collection a ficar vazia se já existir de outro teste
    try:
        store.client.delete_collection("collection_vazia_teste")
    except Exception:
        pass
    
    # Recria limpa
    store = VectorStoreManager(collection_name="collection_vazia_teste")
    
    resultado = store.buscar_contexto("Qualquer termo aleatório")
    assert resultado == []

def test_vectorstore_multiplos_documentos_e_relevancia():
    """
    Scenario: Inserir múltiplos documentos e garantir que o n_results traz o mais relevante.
    """
    store = VectorStoreManager(collection_name="collection_multipla_teste")
    
    # Adiciona documentos de temas diferentes
    store.adicionar_documento(doc_id="doc1", texto="Python é uma linguagem de programação muito popular para IA.")
    store.adicionar_documento(doc_id="doc2", texto="Receitas de bolo de cenoura levam três cenouras médias e cobertura de chocolate.")
    store.adicionar_documento(doc_id="doc3", texto="Machine Learning e Deep Learning utilizam redes neurais profundas.")
    
    # Busca por um tema específico limitando a 1 resultado
    resultado = store.buscar_contexto("Como fazer bolos?", n_results=1)
    
    assert len(resultado) == 1
    assert "bolo de cenoura" in resultado[0]