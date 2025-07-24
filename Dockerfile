# Use a imagem base leve do Python
FROM python:3.9-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Instala as dependências do sistema necessárias
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia o arquivo de requisitos primeiro para aproveitar o cache do Docker
COPY requirements.txt .

# Instala as dependências do Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia o restante dos arquivos da aplicação
COPY . .

# Cria diretório para downloads se não existir
RUN mkdir -p /app/downloads

# Expõe a porta que a aplicação vai rodar
EXPOSE 3333

# Comando para rodar a aplicação
CMD ["uvicorn", "api_backend:app", "--host", "0.0.0.0", "--port", "3333"]
