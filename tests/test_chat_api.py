import pytest
from fastapi.testclient import TestClient
from src.app import app, orchestrator

client = TestClient(app)

@pytest.fixture(autouse=True)
def limpar_historico_agente():
    """Limpa o histórico do orquestrador antes de cada teste rodar."""
    orchestrator.message_history.clear()
    yield


"""
Gherkin:
    Scenario: API key is up and running
        Given the API is running
        When a GET request is made to the root endpoint
        Then the response status code should be 200
"""
def test_api_key_is_up_and_running():
    """
    Scenario: API key is up and running (com checagem real do Gemini)
    """
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["gemini_api"] == "connected" # Garante que o Google respondeu com sucesso!

"""
Gherkin:
  Scenario: User sends a blank message and receives a error response
    Given the user is connected to the chat API
    When the user sends a message
    Then the user receives a error response
"""
def test_chat_payload_vazio_ou_invalido():
    """
    Scenario: Enviar um payload vazio ou sem a chave 'message' deve retornar erro 422 (Unprocessable Entity).
    """
    response = client.post("/api/chat", json={})
    assert response.status_code == 422

"""
Gherkin:

  Scenario: User sends a message and receives a response
    Given the user is connected to the chat API
    When the user sends a message
    Then the user receives a response

"""
def test_user_sends_message_and_receives_response_from_gemini():
    """
    Scenario: User sends a message and receives a response from Gemini
    """
    # GIVEN the user is connected to the chat API
    payload = {"message": "Responda apenas com a palavra: PING"}
    
    # WHEN
    response = client.post("/api/chat", json=payload)
    
    # THEN the user receives a response
    assert response.status_code == 200
    
    data = response.json()
    assert "response" in data
    assert isinstance(data["response"], str)
    assert len(data["response"]) > 0 # coerente, resposta não vazia

    #print("Resposta do Gemini:", data["response"])  # Para debug, mostra a resposta real do Gemini


"""
Gherkin:
  Scenario: User submits feedback to improve the agent's prompt
    Given a feedback payload with a suggestion
    When the user sends the feedback to the API
    Then the API accepts it successfully
    And confirms the prompt update
"""
def test_feedback_updates_agent_system_prompt():
    """
    Scenario: Feedback uses a real message_id from chat history to update the agent's prompt
    """
    # 1. GIVEN: O usuário envia uma mensagem primeiro para gerar um message_id real no histórico
    chat_payload = {"message": "Olá, eu sou um usuário formal."}
    chat_response = client.post("/api/chat", json=chat_payload)
    
    assert chat_response.status_code == 200
    chat_data = chat_response.json()
    real_message_id = chat_data["message_id"] # Capturamos o ID gerado pelo bot
    
    # 2. WHEN: O usuário envia o feedback referenciando esse message_id real
    feedback_payload = {
        "message_id": real_message_id, # Usando o ID dinâmico obtido do chat
        "rating": 1,
        "feedback_text": "Você foi formal demais.",
        "suggested_improvement": "A partir de agora, responda sempre de forma muito descontraída e com gírias."
    }
    
    response = client.post("/api/feedback", json=feedback_payload)
    
    # 3. THEN: A API aceita e atualiza o prompt com base na interação real
    # Falha aqui tambem indica que o tratamento de feedback com erro está impedindo nova versão de prompt
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "new_prompt_version" in data


def test_feedback_com_message_id_de_erro():
    """
    Scenario: Tentar enviar um feedback utilizando message_id="error" deve ser rejeitado pelo orquestrador/API.
    """
    feedback_payload = {
        "message_id": "error",
        "rating": 1,
        "feedback_text": "Isso não deveria funcionar."
    }
    
    response = client.post("/api/feedback", json=feedback_payload)
    
    assert response.status_code == 400
    assert "Não é possível enviar feedback" in response.json()["detail"]