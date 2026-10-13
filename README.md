# 🎬 YT Web Analyzer - Downloader API

API autônoma desenvolvida em **FastAPI + yt-dlp + FFmpeg** para baixar vídeos de qualquer rede social/plataforma (YouTube, TikTok, Instagram, Twitter/X, etc.), converter para formato `MP4 (H.264/AAC)` otimizado para navegadores e entregar com autenticação segura.

---

## 🔒 Autenticação

A API protege os endpoints `POST /api/download` e `POST /api/info` com chave de segurança.

Defina a variável de ambiente:
```bash
API_KEY=sua_chave_secreta_aqui
```
*(Você também pode criar um arquivo `.env` na pasta da API com base no `.env.example`)*

### Como autenticar requisições:
Envie a chave através de qualquer um dos cabeçalhos HTTP:
- `X-API-Key: sua_chave_secreta_aqui`
- Ou `Authorization: Bearer sua_chave_secreta_aqui`

> Se a variável `API_KEY` **não** for configurada, a API funcionará em modo aberto/público.

---

## 🚀 Como Subir a API Separada

### Opção 1: Render (Gratuito / Cloud)
1. Crie uma conta no [Render](https://render.com).
2. Clique em **New +** -> **Web Service**.
3. Conecte este repositório Git (`yt-web-analyzer`).
4. Configure:
   - **Environment:** `Docker` (recomendado) ou `Python 3`.
   - Se escolher Python:
     - **Build Command:** `apt-get update && apt-get install -y ffmpeg && pip install -r requirements.txt`
     - **Start Command:** `uvicorn server:app --host 0.0.0.0 --port $PORT`
5. Em **Environment Variables**, adicione:
   - `API_KEY`: `sua_chave_secreta_aqui`
6. Clique em **Deploy**. A sua URL pública será algo como `https://sua-api.onrender.com`.

### Opção 2: Railway
1. Crie um projeto no [Railway](https://railway.app).
2. Selecione **Deploy from GitHub repo**.
3. Adicione a variável `API_KEY` nas configurações.
4. O Railway detectará o `Dockerfile` automaticamente.

### Opção 3: Usando Docker (VPS / Local)
```bash
docker build -t autocutter-api .
docker run -d -p 8000:8000 -e API_KEY=sua_chave_secreta autocutter-api
```

---

## 🔗 Conectando o Frontend ao Servidor

No site (`index.html`), clique no botão **⚙️ Configurar API**:
1. **URL da API:** insira a URL pública da sua API (ex.: `https://sua-api.onrender.com`).
2. **Chave de Autenticação (API Key):** insira a mesma chave definida na variável `API_KEY`.
3. Clique em **Salvar Configurações**.

A configuração fica salva no navegador do usuário via `localStorage`.

---

## 📡 Endpoints

| Método | Rota | Autenticação | Descrição |
|---|---|---|---|
| `GET` | `/health` | Pública | Status da API e se exige autenticação |
| `POST` | `/api/info` | Obrigatória | Metadados do vídeo (título, duração, thumbnail) |
| `POST` | `/api/download` | Obrigatória | Download do vídeo MP4 compatível com o navegador |
