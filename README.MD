# Chatbot com Feedback Dinâmico

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-backend-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-frontend-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Gemini](https://img.shields.io/badge/Google%20Gemini-function%20calling-4285F4?logo=google&logoColor=white)](https://ai.google.dev/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-RAG-F15A24)](https://www.trychroma.com/)

## Descrição do projeto

Chatbot desacoplado para conversação com contexto, execução de ferramentas externas e autoaperfeiçoamento orientado por feedback. A interface Streamlit envia requisições ao backend FastAPI, que coordena o histórico, recupera contexto no ChromaDB (RAG) e delega a resposta ao Google Gemini.

Fluxo principal: `Streamlit -> FastAPI -> Orchestrator -> ChromaDB (RAG) -> Gemini`. O agente combina o contexto recuperado, o histórico recente e o prompt vigente. O Gemini responde diretamente ou aciona uma Tool por *Function Calling*; o orquestrador então devolve a resposta e registra a interação.

O agente usa *Function Calling* automático para decidir quando consultar ViaCEP ou PokéAPI. Cada resposta recebe um `message_id`; o usuário pode avaliá-la de 1 a 5 e enviar uma sugestão. O agente então reescreve seu *system prompt*, mantém versões em memória e utiliza a versão atual nas próximas interações. O histórico conversacional é limitado às 10 interações mais recentes.

## Instruções de instalação e execução

Pré-requisitos: Python 3.10+, acesso à internet e uma chave da API Gemini.

**Windows (PowerShell)**

```powershell
git clone <URL_DO_REPOSITORIO>
cd teste_tecnico
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install .
```

**Linux/macOS (bash/zsh)**

```bash
git clone <URL_DO_REPOSITORIO>
cd teste_tecnico
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install .
```

Crie um arquivo `.env` na raiz (não versionado):

```env
GEMINI_API_KEY=sua_chave_gemini
```

Inicialize a base vetorial e abra dois terminais, mantendo o ambiente virtual ativo:

```powershell
python .\src\vectorstore\loader.py
uvicorn src.app:app --reload
```

No Linux/macOS, use os mesmos comandos com caminhos POSIX:

```bash
python src/vectorstore/loader.py
uvicorn src.app:app --reload
```

Em outro terminal, inicie o frontend:

```powershell
cd teste_tecnico
.\.venv\Scripts\Activate.ps1
streamlit run .\ui\frontend.py
```

```bash
streamlit run ./ui/frontend.py
```

Acesse `http://localhost:8501`. A API fica disponível em `http://localhost:8000` e sua documentação interativa em `http://localhost:8000/docs`.

Para executar os testes:

```powershell
pip install ".[test]"
python -m pytest
```

## Instruções para rodar com Docker

Defina `GEMINI_API_KEY` no ambiente ou em um arquivo `.env` na raiz e execute:

```powershell
docker compose up --build
```

O Compose inicia a API em `http://localhost:8000` e a interface em `http://localhost:8501`. Para executar a suíte de testes no serviço dedicado:

```powershell
docker compose run --rm tests
```

Para encerrar os serviços:

```powershell
docker compose down
```

## Exemplos de uso

Na interface, envie uma pergunta pelo campo de chat. Exemplos que acionam as tools:

- `Consulte o CEP 01001-000 e informe o endereço.`
- `Quais são os tipos, peso e habilidades do Pikachu?`

O Gemini identifica a intenção, chama `consultar_cep` ou `consultar_pokemon` e apresenta os dados tratados na resposta. CEPs são normalizados para oito dígitos; a PokéAPI recebe o nome ou ID em minúsculas.

Fluxo de avaliação: envie uma mensagem, abra **Avaliar esta resposta**, selecione uma nota e informe o comentário. O backend gera uma nova versão do prompt. Notas 1–2 aplicam ajuste crítico, 3 ajuste moderado e 4–5 refinamento positivo. A alteração é mantida em memória durante a execução do backend.

Exemplo de avaliação via HTTP desacoplada (com servidor rodando):

```powershell
$chat = Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/api/chat `
  -ContentType "application/json" `
  -Body '{"message":"Responda de forma objetiva."}'

Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/api/feedback `
  -ContentType "application/json" `
  -Body (@{
    message_id = $chat.message_id
    rating = 4
    feedback_text = "Boa resposta; mantenha a objetividade."
  } | ConvertTo-Json)
```

Em caso de falha no processamento, a UI oferece **Tentar novamente (Retry)**, que reenvia a última mensagem para `/api/chat/retry`.

## Documentação das APIs utilizadas

### APIs internas

| Método e rota | Entrada | Resultado |
|---|---|---|
| `POST /api/chat` | `{ "message": "..." }` | `{ "message_id": "...", "response": "..." }` |
| `POST /api/feedback` | `message_id`, `rating`, `feedback_text` e `suggested_improvement` opcional | Confirma a atualização e retorna `new_prompt_version` |
| `POST /api/chat/retry` | `{ "message": "..." }` | Reprocessa a mensagem e retorna uma nova resposta |

Payloads ausentes ou inválidos retornam `422`. Feedback para uma mensagem inexistente ou com ID `error` retorna `400`.

### APIs externas integradas como Tools

- **ViaCEP:** `GET https://viacep.com.br/ws/{cep}/json/`. A tool remove formatação, valida oito dígitos e retorna logradouro, bairro, localidade e UF. Trata CEP inexistente, status HTTP e falhas de conexão.
- **PokéAPI:** `GET https://pokeapi.co/api/v2/pokemon/{nome_ou_id}`. A tool retorna nome, ID, altura, peso, tipos e habilidades, tratando Pokémon inexistente, status HTTP e falhas de conexão.

As respostas de erro das tools são normalizadas como dicionários com a chave `erro`, permitindo que o agente comunique a falha sem interromper o fluxo.
