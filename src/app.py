# Rodar servidor uvicorn src.app:app --reload
# Rodar front streamlit run .\ui\frontend.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from src.orchestrator.engine import ChatOrchestrator

# Inicialização da aplicação
app = FastAPI(title="API do Chatbot IA com Feedback")

orchestrator = ChatOrchestrator()

# Definem exatamente o que a API espera receber e o que ela vai devolver.
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    message_id: str
    response: str

class FeedbackRequest(BaseModel):
    message_id: str
    rating: int  # Nota de 1 a 5, por exemplo
    feedback_text: str
    suggested_improvement: Optional[str] = None

class FeedbackResponse(BaseModel):
    status: str
    new_prompt_version: Optional[str] = None  # Novo prompt atualizado, se aplicável

class RetryRequest(BaseModel):
    message: str  # Ou message_id, caso queira buscar a última mensagem direto do histórico

# --- Rotas (Endpoints) ---
# Adicione esta rota no seu src/main.py
@app.get("/")
async def root():
    """
    Endpoint raiz para verificar se a API está online.
    """
    # Testa a conexão com o Gemini
    if orchestrator.agent.testar_conexao():
        return {"status": "online", "gemini_api": "connected"}
    else:
        return {"status": "online", "gemini_api": "disconnected"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint para chat: com mensagens do usuário e retornar respostas do agente de IA.
    """
    resultado = await orchestrator.processar_mensagem(request.message)
    return ChatResponse(
        message_id=resultado["message_id"],
        response=resultado["response"]
    )

@app.post("/api/chat/retry", response_model=ChatResponse)
async def retry_chat_endpoint(request: RetryRequest):
    """
    Endpoint de Replay: Tenta reprocessar a última requisição do usuário caso tenha ocorrido um erro.
    """
    try:
        # Reutiliza o mesmo fluxo do orquestrador para gerar uma nova resposta
        resultado = await orchestrator.processar_mensagem(request.message)
        
        if resultado["message_id"] == "error":
            return ChatResponse(
                message_id="retry_error",
                response="A tentativa de reenvio falhou novamente. Por favor, tente mais tarde."
            )
            
        return ChatResponse(
            message_id=resultado["message_id"],
            response=resultado["response"]
        )
    except Exception as e:
        return ChatResponse(
            message_id="error",
            response=f"Erro crítico no replay: {str(e)}"
        )

@app.post("/api/feedback", response_model=FeedbackResponse)
async def feedback_endpoint(request: FeedbackRequest):
    """
    Endpoint para receber feedback do usuário e atualizar o system prompt do agente.
    """
    sugestao = request.suggested_improvement or request.feedback_text
    try:
        # Repassamos o rating (peso) junto com o ID e a sugestão
        novo_prompt = await orchestrator.processar_feedback(
            message_id=request.message_id, 
            rating=request.rating, 
            sugestao=sugestao
        )
        
        return FeedbackResponse(
            status="success",
            new_prompt_version=novo_prompt
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))