# Painel Administrativo Auvo

Este projeto é um painel administrativo moderno feito em React, que consome a API local (FastAPI) para gerenciar e visualizar todos os dados sincronizados da Auvo.

## Como iniciar

1. Instale as dependências:
   ```bash
   npm install
   ```
2. Inicie o painel:
   ```bash
   npm start
   ```

## Estrutura sugerida
- `src/pages` — Páginas principais (Dashboard, Usuários, Tarefas, Clientes, etc)
- `src/components` — Componentes reutilizáveis (Tabela, Filtros, Sidebar, etc)
- `src/services` — Serviços para consumir a API backend
- `src/styles` — Estilos globais e temas

## Requisitos
- Node.js >= 16
- Conexão com a API backend rodando em http://localhost:8000

---

### Para produção

- Use `npm run build` para gerar os arquivos otimizados.

---

Sinta-se livre para customizar o painel conforme as necessidades do seu negócio!
