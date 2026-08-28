FROM python:3.10-slim

WORKDIR /app

# Instala dependências do sistema essenciais para compilação
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia o descritor de dependências primeiro para aproveitar o cache do Docker
COPY pyproject.toml ./

# Instala o projeto e as dependências (incluindo o grupo opcional de testes)
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .[test]

# Copia o código-fonte e os testes para dentro do container
COPY src/ ./src/
COPY tests/ ./tests/

# Executa o script do vector store no momento do build para popular o banco inicial
RUN python -c "from src.vectorstore.loader import inicializar_e_popular_rag; inicializar_e_popular_rag()"

# Expõe a porta padrão do FastAPI
EXPOSE 8000

# Comando padrão para iniciar a API
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]