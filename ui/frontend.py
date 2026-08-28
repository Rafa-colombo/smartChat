import streamlit as st
import requests
import os

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# Configuração da página
st.set_page_config(
    page_title="Chatbot com Feedback Dinâmico",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 Chatbot Inteligente com RAG & Tools")
st.markdown("Converse com o agente, consulte CEPs, Pokémons e avalie as respostas para atualizar o comportamento do bot em tempo real!")

# Inicializa o histórico de mensagens na sessão do Streamlit para manter a UI fluida
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe o histórico de mensagens na tela
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # Se for mensagem do assistente e tiver um message_id válido, mostra a opção de feedback
        if message["role"] == "assistant" and "message_id" in message and message["message_id"] != "error":
            with st.expander("⭐ Avaliar esta resposta"):
                rating = st.slider("Nota (1 a 5):", 1, 5, 3, key=f"slider_{message['message_id']}")
                feedback_text = st.text_input("O que você achou?", key=f"text_{message['message_id']}")
                suggested_improvement = st.text_input("Sugestão de melhoria (opcional):", key=f"sug_{message['message_id']}")
                
                # Dentro do trecho do feedback no Streamlit:
                if st.button("Enviar Feedback", key=f"btn_{message['message_id']}"):
                    payload_feedback = {
                        "message_id": message["message_id"],
                        "rating": rating,
                        "feedback_text": feedback_text or "Feedback enviado pelo usuário",
                        "suggested_improvement": suggested_improvement
                    }
                    
                    # Carregamento ativo durante a requisição de atualização de prompt
                    with st.spinner("🔄 Atualizando comportamento do agente com base no seu feedback..."):
                        try:
                            res = requests.post(f"{API_URL}/api/feedback", json=payload_feedback)
                            if res.status_code == 200:
                                data = res.json()
                                st.success("Feedback enviado com sucesso! Prompt do agente atualizado.")
                                st.info(f"**Nova Versão do Prompt:** {data.get('new_prompt_version')}")
                            else:
                                st.error(f"Erro ao enviar feedback: {res.json().get('detail', 'Erro desconhecido')}")
                        except Exception as e:
                            st.error(f"Falha de conexão com a API: {e}")

        # Quando a mensagem do assistente for um erro ("error" ou "retry_error"):
        elif message["role"] == "assistant" and message.get("message_id") == "error":
            # Encontra qual foi a última mensagem enviada pelo usuário para poder reenviar
            user_messages = [m["content"] for m in st.session_state.messages if m["role"] == "user"]
            ultima_mensagem_usuario = user_messages[-1] if user_messages else ""

            if st.button("🔄 Tentar novamente (Retry)", key=f"retry_{len(st.session_state.messages)}"):
                with st.spinner("Reenviando requisição..."):
                    try:
                        # Chama a rota /api/chat/retry que você criou no FastAPI
                        payload_retry = {"message": ultima_mensagem_usuario}
                        res = requests.post(f"{API_URL}/api/chat/retry", json=payload_retry)
                        
                        if res.status_code == 200:
                            data = res.json()
                            # Atualiza a última mensagem do assistente no histórico com a nova resposta bem-sucedida
                            st.session_state.messages[-1] = {
                                "role": "assistant",
                                "content": data["response"],
                                "message_id": data["message_id"]
                            }
                            st.success("Reaproveitamento realizado com sucesso!")
                            st.rerun()
                        else:
                            st.error("A tentativa de retry falhou na API.")
                    except Exception as e:
                        st.error(f"Erro de conexão ao tentar o retry: {e}")


# Entrada de texto do usuário (Chat Input)
if prompt := st.chat_input("Digite sua mensagem aqui..."):
    # Adiciona a mensagem do usuário ao histórico visual
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Envia para a API do FastAPI
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                response = requests.post(f"{API_URL}/api/chat", json={"message": prompt})
                if response.status_code == 200:
                    res_data = response.json()
                    bot_response = res_data["response"]
                    message_id = res_data["message_id"]
                    
                    st.markdown(bot_response)
                    
                    # Salva no histórico da sessão
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": bot_response,
                        "message_id": message_id
                    })
                    # Recarrega a página para renderizar o expander de feedback da nova mensagem
                    st.rerun()
                else:
                    st.error("Erro na comunicação com o backend.")
            except Exception as e:
                st.error(f"Não foi possível conectar ao servidor FastAPI em {API_URL}. Certifique-se de que ele está rodando. Erro: {e}")