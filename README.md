# DocMind Backend

Backend do DocMind, um Copiloto Inteligente de Analise Documental empresarial. Esta fundacao prepara a API para evoluir em etapas futuras com processamento de PDFs, chunks, embeddings, vetores no PostgreSQL com pgvector e RAG com respostas baseadas em fontes.

Nesta etapa, o projeto inclui a base tecnica da API, configuracao de banco, estrutura modular, autenticacao inicial com cadastro, login, JWT, usuario autenticado, CRUD de workspaces por usuario, upload inicial de PDFs, extracao simples de texto por pagina, chunking local por caracteres, embeddings locais nos chunks com pgvector, busca semantica, RAG basico com Ollama, modos iniciais de analise documental, historico simples de chat para perguntas RAG, agente roteador de intencao por regras, comparacao entre documentos e endpoints agregados de dashboard backend. OCR, LangChain, LangGraph, agentes complexos, frontend e graficos visuais ainda nao foram implementados.

## Stack

- Python
- FastAPI
- Uvicorn
- SQLAlchemy
- Alembic
- PostgreSQL
- pgvector
- Pydantic
- pydantic-settings
- python-dotenv
- passlib + bcrypt
- python-jose
- python-multipart
- pypdf
- pgvector
- sentence-transformers
- httpx
- Docker Compose

## Criar ambiente virtual

```bash
python -m venv .venv
```

Ative o ambiente virtual:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# Linux/macOS
source .venv/bin/activate
```

## Instalar dependencias

```bash
pip install -r requirements.txt
```

## Configurar variaveis de ambiente

Crie um arquivo `.env` a partir do exemplo:

```bash
cp .env.example .env
```

No Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

## Subir o banco com Docker Compose

```bash
docker compose up -d
```

O PostgreSQL sobe na porta `5432` usando a imagem `pgvector/pgvector:pg16`.

## Rodar a API

```bash
uvicorn app.main:app --reload
```

## Rodar migrations

Com o banco no ar, aplique as migrations:

```bash
alembic upgrade head
```

## Acessar a rota de health

Abra:

```text
http://localhost:8000/health
```

Resposta esperada:

```json
{
  "status": "ok",
  "app_name": "DocMind API",
  "environment": "development"
}
```

## Acessar a documentacao

Abra:

```text
http://localhost:8000/docs
```

## Testar cadastro

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Felipe Buzziol",
    "email": "felipe@example.com",
    "password": "Admin123!"
  }'
```

## Testar login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "felipe@example.com",
    "password": "Admin123!"
  }'
```

A resposta retorna `access_token`, `token_type` e `user`.

## Testar usuario autenticado

Use o token retornado no login:

```bash
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer <access_token>"
```

## Testar criacao de workspace

Use o token retornado no login:

```bash
curl -X POST http://localhost:8000/workspaces \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Contratos",
    "description": "Workspace para analise de contratos empresariais"
  }'
```

## Testar listagem de workspaces

```bash
curl http://localhost:8000/workspaces \
  -H "Authorization: Bearer <access_token>"
```

## Testar busca de workspace por id

```bash
curl http://localhost:8000/workspaces/<workspace_id> \
  -H "Authorization: Bearer <access_token>"
```

## Testar atualizacao de workspace

```bash
curl -X PATCH http://localhost:8000/workspaces/<workspace_id> \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Contratos Juridicos",
    "description": "Contratos e documentos juridicos"
  }'
```

## Testar delecao de workspace

```bash
curl -X DELETE http://localhost:8000/workspaces/<workspace_id> \
  -H "Authorization: Bearer <access_token>"
```

Resposta esperada:

```json
{
  "message": "Workspace deleted successfully"
}
```

## Testar upload de documento PDF

Nesta etapa, o PDF e apenas salvo localmente e registrado no banco. Ele ainda nao e processado por IA.

```bash
curl -X POST http://localhost:8000/workspaces/<workspace_id>/documents \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@/caminho/para/contrato.pdf;type=application/pdf"
```

O arquivo precisa ter `content_type` `application/pdf`, extensao `.pdf` e tamanho maximo definido por `MAX_UPLOAD_SIZE_MB`.

## Testar listagem de documentos

```bash
curl http://localhost:8000/workspaces/<workspace_id>/documents \
  -H "Authorization: Bearer <access_token>"
```

## Testar busca de documento por id

```bash
curl http://localhost:8000/documents/<document_id> \
  -H "Authorization: Bearer <access_token>"
```

## Testar delecao de documento

```bash
curl -X DELETE http://localhost:8000/documents/<document_id> \
  -H "Authorization: Bearer <access_token>"
```

Resposta esperada:

```json
{
  "message": "Document deleted successfully"
}
```

## Processar documento PDF

O processamento desta etapa e sincrono, extrai apenas texto ja presente no PDF e salva o conteudo por pagina. Nao ha OCR nem RAG.

```bash
curl -X POST http://localhost:8000/documents/<document_id>/process \
  -H "Authorization: Bearer <access_token>"
```

Resposta esperada:

```json
{
  "id": "...",
  "workspace_id": "...",
  "original_filename": "contrato.pdf",
  "stored_filename": "...pdf",
  "mime_type": "application/pdf",
  "file_size": 123456,
  "total_pages": 5,
  "status": "PROCESSED",
  "created_at": "...",
  "updated_at": "...",
  "processed_at": "..."
}
```

## Listar paginas extraidas

```bash
curl http://localhost:8000/documents/<document_id>/pages \
  -H "Authorization: Bearer <access_token>"
```

PDFs escaneados podem retornar paginas com texto vazio, pois OCR ainda nao foi implementado.

## Gerar chunks de documento

O documento precisa estar com status `PROCESSED`. Esta etapa ainda nao faz embeddings automaticamente e ainda nao faz RAG.

```bash
curl -X POST http://localhost:8000/documents/<document_id>/chunks \
  -H "Authorization: Bearer <access_token>"
```

Os chunks usam `CHUNK_SIZE` e `CHUNK_OVERLAP` configurados no ambiente.

## Listar chunks de documento

```bash
curl http://localhost:8000/documents/<document_id>/chunks \
  -H "Authorization: Bearer <access_token>"
```

## Gerar embeddings de chunks

Esta etapa usa `sentence-transformers` com o modelo `all-MiniLM-L6-v2` e salva vetores de 384 dimensoes no PostgreSQL com pgvector. A primeira execucao pode baixar o modelo localmente. Ainda nao ha busca semantica, RAG ou chat.

```bash
curl -X POST http://localhost:8000/documents/<document_id>/embeddings \
  -H "Authorization: Bearer <access_token>"
```

Para reprocessar chunks que ja possuem embedding:

```bash
curl -X POST "http://localhost:8000/documents/<document_id>/embeddings?reprocess=true" \
  -H "Authorization: Bearer <access_token>"
```

## Busca semantica por documento

Antes da busca, o documento precisa ter sido processado, chunkado e indexado com embeddings. Esta etapa retorna chunks relevantes com pagina e score; ainda nao usa LLM, nao monta resposta final e nao faz RAG.

```bash
curl -X POST http://localhost:8000/documents/<document_id>/semantic-search \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Quais clausulas falam sobre pagamento?",
    "top_k": 5
  }'
```

## Busca semantica por workspace

```bash
curl -X POST http://localhost:8000/workspaces/<workspace_id>/semantic-search \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "confidencialidade",
    "top_k": 10
  }'
```

## Ollama para RAG

Instale e rode o Ollama localmente. O modelo padrao configurado e `llama3.1`.

```bash
ollama pull llama3.1
ollama serve
```

Em outro terminal, confirme o modelo:

```bash
ollama list
```

As variaveis principais sao:

```text
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
RAG_TOP_K=5
RAG_MAX_CONTEXT_CHARS=8000
```

## Perguntar sobre um documento

Antes de perguntar, execute o fluxo completo: upload, processamento, chunks e embeddings. Esta etapa usa fontes recuperadas por busca semantica e chama o Ollama, mas ainda nao implementa modos de analise, agentes, streaming ou historico persistente.

```bash
curl -X POST http://localhost:8000/documents/<document_id>/ask \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quais clausulas falam sobre pagamento?",
    "top_k": 5
  }'
```

## Perguntar sobre um workspace

```bash
curl -X POST http://localhost:8000/workspaces/<workspace_id>/ask \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quais documentos mencionam confidencialidade?",
    "top_k": 10
  }'
```

## Analises documentais

Antes de gerar analises, execute o fluxo completo: upload, processamento, chunks e embeddings. As analises usam fontes recuperadas por busca semantica e Ollama. Esta etapa ainda nao implementa agentes, comparacao de documentos, dashboard, streaming ou historico persistente.

`force=false` retorna a ultima analise salva daquele tipo, quando existir. `force=true` cria uma nova analise e preserva o historico.

Resumo executivo:

```bash
curl -X POST http://localhost:8000/documents/<document_id>/analysis/summary \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "force": false,
    "top_k": 8
  }'
```

Analise de risco:

```bash
curl -X POST http://localhost:8000/documents/<document_id>/analysis/risks \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "force": true,
    "top_k": 10
  }'
```

Extracao estruturada:

```bash
curl -X POST http://localhost:8000/documents/<document_id>/analysis/extract \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "force": false,
    "top_k": 12
  }'
```

Listar analises salvas:

```bash
curl http://localhost:8000/documents/<document_id>/analysis \
  -H "Authorization: Bearer <access_token>"
```

## Historico de chat RAG

Cada chamada bem-sucedida para `/ask` cria uma nova sessao de chat independente, com uma mensagem `USER` e uma mensagem `ASSISTANT`. Ainda nao ha continuidade de conversa, memoria conversacional, streaming ou endpoint para enviar novas mensagens em uma sessao existente.

A resposta de `/ask` inclui `chat_session_id`.

Listar sessoes de um documento:

```bash
curl http://localhost:8000/documents/<document_id>/chat-sessions \
  -H "Authorization: Bearer <access_token>"
```

Listar sessoes de um workspace:

```bash
curl http://localhost:8000/workspaces/<workspace_id>/chat-sessions \
  -H "Authorization: Bearer <access_token>"
```

Consultar mensagens de uma sessao:

```bash
curl http://localhost:8000/chat-sessions/<session_id> \
  -H "Authorization: Bearer <access_token>"
```

Deletar sessao:

```bash
curl -X DELETE http://localhost:8000/chat-sessions/<session_id> \
  -H "Authorization: Bearer <access_token>"
```

## Agente roteador de intencao

O agente recebe uma mensagem em linguagem natural, classifica a intencao por regras simples e chama os fluxos ja existentes. Ele nao usa LangGraph, LangChain, OpenAI, memoria conversacional ou grafo de agentes.

Intencoes suportadas:

- `RAG_QA`
- `SEMANTIC_SEARCH`
- `EXECUTIVE_SUMMARY`
- `RISK_ANALYSIS`
- `DATA_EXTRACTION`

Documento:

```bash
curl -X POST http://localhost:8000/documents/<document_id>/agent \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Resuma esse contrato em pontos principais",
    "top_k": 8,
    "force": false
  }'
```

Workspace:

```bash
curl -X POST http://localhost:8000/workspaces/<workspace_id>/agent \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Quais documentos mencionam confidencialidade?",
    "top_k": 10
  }'
```

No workspace, modos de analise como resumo, riscos e extracao retornam erro, pois nesta etapa estao disponiveis apenas para documentos individuais.

## Comparacao entre documentos

Compare dois documentos do mesmo workspace. Ambos precisam estar processados, chunkados e com embeddings. Esta etapa usa fontes dos dois documentos e Ollama, mas nao implementa diff visual, comparacao lado a lado, LangChain, LangGraph ou agentes complexos.

`force=false` retorna a comparacao mais recente para o mesmo workspace, documentos e tipo. `force=true` gera uma nova comparacao e preserva o historico.

Comparacao geral:

```bash
curl -X POST http://localhost:8000/workspaces/<workspace_id>/comparisons \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "base_document_id": "<document_id_base>",
    "target_document_id": "<document_id_target>",
    "comparison_type": "GENERAL",
    "force": false,
    "top_k": 8
  }'
```

Tipos disponiveis:

- `GENERAL`
- `RISKS`
- `FINANCIAL`
- `DATES`
- `OBLIGATIONS`

Listar comparacoes:

```bash
curl http://localhost:8000/workspaces/<workspace_id>/comparisons \
  -H "Authorization: Bearer <access_token>"
```

Buscar comparacao por id:

```bash
curl http://localhost:8000/comparisons/<comparison_id> \
  -H "Authorization: Bearer <access_token>"
```

Deletar comparacao:

```bash
curl -X DELETE http://localhost:8000/comparisons/<comparison_id> \
  -H "Authorization: Bearer <access_token>"
```

## Dashboard backend

Os endpoints de dashboard retornam contagens e listas recentes para alimentar um frontend. Eles nao chamam Ollama, sentence-transformers, busca semantica, processamento de PDF, chunking ou embeddings. Tambem nao retornam conteudo completo de chunks, mensagens, analises ou comparacoes.

Metricas retornadas:

- total de workspaces e documentos;
- documentos por status;
- totais de documentos processados, com falha e enviados;
- total de chunks e chunks com embedding;
- total de analises, comparacoes e sessoes de chat;
- documentos, analises, comparacoes e sessoes recentes.

Dashboard global do usuario:

```bash
curl "http://localhost:8000/dashboard?recent_limit=5" \
  -H "Authorization: Bearer <access_token>"
```

Dashboard de um workspace:

```bash
curl "http://localhost:8000/workspaces/<workspace_id>/dashboard?recent_limit=5" \
  -H "Authorization: Bearer <access_token>"
```

`recent_limit` e opcional, com minimo `1`, maximo `20` e default `5`.

## Alembic

O Alembic ja esta configurado para usar o `Base.metadata` de `app.core.database`. Para gerar novas migrations depois de criar modelos SQLAlchemy:

```bash
alembic revision --autogenerate -m "create initial tables"
```

E aplicar migrations com:

```bash
alembic upgrade head
```
