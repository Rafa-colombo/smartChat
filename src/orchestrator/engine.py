import uuid
from src.agent.bot import ChatbotAgent
from src.vectorstore.store import VectorStoreManager

class ChatOrchestrator:
    def __init__(self, max_history: int = 10):
        self.agent = ChatbotAgent()
        self.vector_store = VectorStoreManager()
        self.message_history = []
        self.max_history = max_history

    async def processar_mensagem(self, mensagem: str) -> dict:
        """
        ORquestrador: Recebe a mensagem do usuário, busca contexto relevante na base vetorial (RAG),
        decide se precisa chamar uma tool (dentro do agente), e retorna a resposta.
        """
        try:
            # 1. ORQUESTRAÇÃO DE RAG: Sempre busca contexto base para enriquecer a resposta
            contextos = self.vector_store.buscar_contexto(mensagem)
            contexto_texto = "\n".join(contextos) if contextos else "Nenhum contexto adicional."

            # 2. DECISÃO DINÂMICA DE TOOLS VIA AGENTE
            resultado_agente = self.agent.gerar_resposta_com_contexto(mensagem, contexto_texto, self.message_history)
            
            message_id = str(uuid.uuid4())[:8]
            
            interacao = {
                "message_id": message_id,
                "user_message": mensagem,
                "bot_response": resultado_agente
            }
            
            # 3. Gerencia o histórico centralizado no orquestrador
            self.message_history.append(interacao)
            if len(self.message_history) > self.max_history:
                self.message_history.pop(0)  
            
            return {
                "message_id": message_id,
                "response": resultado_agente
            }
        except Exception as e:
            # Erros geram um ID "error" e NÃO entram no histórico de feedback
            return {
                "message_id": "error",
                "response": f"Desculpe, ocorreu um erro ao processar sua solicitação: {str(e)}"
            }

    async def processar_feedback(self, message_id: str, rating: int, sugestao: str) -> str:
        """Valida o ID no histórico do orquestrador e comanda a atualização do prompt."""
        if message_id == "error":
            raise ValueError("Não é possível enviar feedback para uma mensagem que resultou em erro.")

        # Busca a interação no histórico gerenciado pelo orquestrador
        interacao_alvo = next((item for item in self.message_history if item["message_id"] == message_id), None)
        
        if not interacao_alvo:
            raise ValueError(f"Mensagem com ID '{message_id}' não foi encontrada no histórico.")

        # Delega ao agente apenas a lógica de reescrita de prompt usando os dados validados
        novo_prompt = self.agent.atualizar_prompt(
            user_message=interacao_alvo["user_message"],
            bot_response=interacao_alvo["bot_response"],
            rating=rating,
            sugestao=sugestao
        )
        return novo_prompt