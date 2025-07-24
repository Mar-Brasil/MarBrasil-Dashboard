# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Copia os arquivos de dependência
COPY package*.json ./

# Instala as dependências
RUN npm install

# Copia o restante dos arquivos
COPY . .

# Constrói a aplicação
RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

# Instala o serve para servir os arquivos estáticos
RUN npm install -g serve

# Copia os arquivos de build
COPY --from=build /app/build /app/build

# Expõe a porta 80
EXPOSE 80

# Inicia o servidor de arquivos estáticos
CMD ["serve", "-s", "build", "-l", "80"]
