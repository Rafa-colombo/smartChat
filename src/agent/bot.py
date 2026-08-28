import google.generativeai as genai
import os
import uuid
from dotenv import load_dotenv
# Tools
from src.tools.viacep import consultar_cep
from src.tools.pokeapi import consultar_pokemon

# Carrega as variáveis do arquivo .env 
load_dotenv()

class ChatbotAgent:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("A variável de ambiente GEMINI_API_KEY não foi encontrada!")
            
        genai.configure(api_key=api_key)
        self.tools = [consultar_cep, consultar_pokemon] # lista de tools para o modelo
        
        modelos_candidatos = ['gemini-3.6-flash', 'gemini-3.5-flash', 'gemini-3.1-flash-lite', 'gemini-3.5-flash-lite']
        self.model = None

        # Laço para testar e encontrar o primeiro modelo disponível - fallback de agente
        for nome_modelo in modelos_candidatos:
            try:
                candidato = genai.GenerativeModel(nome_modelo, tools=self.tools)
                # Testa uma chamada rápida para validar se o modelo está acessível
                candidato.generate_content("ping")
                self.model = candidato
                print(f"[Agente] Sucesso ao inicializar com o modelo: {nome_modelo}") # mudar para log
                break
            except Exception as e:
                print(f"[Agente] Aviso: Falha ao carregar o modelo {nome_modelo}: {str(e)}")
                continue

        # Se nenhum modelo da lista funcionou -> erro crítico
        if self.model is None:
            raise ConnectionError("Nenhum dos modelos Gemini configurados está disponível no momento.")
        
        # Prompt utilizado pelo sistema e atualizado com feedback
        self.current_system_prompt = "Você é um assistente prestativo, claro e objetivo."
        self.prompt_versions = [self.current_system_prompt] # Histórico de versões do prompt 

    def testar_conexao(self) -> bool:
        """Faz uma chamada real e leve para testar se a chave e a internet estão ativas."""
        try:
            resposta = self.model.generate_content("test")
            return bool(resposta.text)
        except Exception as e:
            raise ConnectionError(f"Falha na comunicação com o Gemini (Chave inválida ou sem internet): {str(e)}")

    def _aplicar_guardrails(self, texto: str) -> str:
        """Exemplo de Guardrail: Garante que a resposta não está vazia e filtra conteúdos indesejados."""
        if not texto or len(texto.strip()) == 0:
            return "Desculpe, não consegui processar uma resposta adequada no momento."
        return texto

    def gerar_resposta_com_contexto(self, mensagem_usuario: str, contexto_rag: str = "", historico: list = None) -> str:
        """Gera apenas o texto da resposta baseado na IA e ferramentas."""
        chat = self.model.start_chat(enable_automatic_function_calling=True)

        # Reconstrói o histórico no chat do Gemini se houver histórico passado
        if historico:
            for h in historico:
                chat.history.append({"role": "user", "parts": [h["user_message"]]})
                chat.history.append({"role": "model", "parts": [h["bot_response"]]})

        prompt_completo = (
            f"Instruções do Sistema: {self.current_system_prompt}\n"
            f"Contexto Recuperado (RAG):\n{contexto_rag}\n\n"
            f"Mensagem do Usuário: {mensagem_usuario}"
        )
        resposta = chat.send_message(prompt_completo)
        return self._aplicar_guardrails(resposta.text)

    def atualizar_prompt(self, user_message: str, bot_response: str, rating: int, sugestao: str) -> str:
        """Reescreve o system prompt com base no feedback e contexto fornecido pelo orquestrador."""
        if rating <= 2:
            urgencia = "URGENTE/CRÍTICO: O usuário odiou o resultado. Corrija essa postura radicalmente."
        elif rating == 3:
            urgencia = "MODERADO: O usuário achou mediano. Faça ajustes pontuais."
        else:
            urgencia = "POSITIVO: Refinamento sutil."

        contexto_falha = (
            f"Contexto da interação:\n"
            f"- Pergunta do Usuário: '{user_message}'\n"
            f"- Resposta anterior do Bot: '{bot_response}'\n"
        )

        meta_prompt = (
            f"Engenheiro de prompts. Prompt atual: '{self.current_system_prompt}'. "
            f"{contexto_falha}Rating: {rating} ({urgencia}). Sugestão: '{sugestao}'. "
            f"Reescreva o prompt do sistema. Retorne APENAS o texto do novo prompt."
        )
        
        try:
            novo_prompt_obj = self.model.generate_content(meta_prompt)
            novo_prompt = novo_prompt_obj.text.strip()
            self.current_system_prompt = novo_prompt
            self.prompt_versions.append(novo_prompt)
            return novo_prompt
        except Exception as e:
            return self.current_system_prompt # Fallback caso a reescrita falhe: mantém o prompt atual