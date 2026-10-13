import os
import re
import secrets
import shutil
import tempfile
import unicodedata
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from starlette.background import BackgroundTask
import yt_dlp

# Carrega variáveis do arquivo .env local se existir
def load_dotenv():
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    if k and k not in os.environ:
                        os.environ[k] = v

load_dotenv()

API_KEY = (os.getenv("API_KEY") or os.getenv("AUTH_TOKEN") or os.getenv("PASSWORD") or "").strip()

app = FastAPI(title="Auto Cutter Video Downloader API", version="1.0.0")

# Habilita CORS irrestrito para aceitar requisições de qualquer frontend (Vercel, Netlify, localhost, file://)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Length"],
)

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": str(exc.detail), "detail": str(exc.detail)}
    )

# Esquemas de cabeçalho de autenticação (X-API-Key e Bearer token)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_auth = HTTPBearer(auto_error=False)

def verify_auth(
    header_key: Optional[str] = Security(api_key_header),
    bearer: Optional[HTTPAuthorizationCredentials] = Security(bearer_auth),
):
    """
    Verifica se a requisição possui a chave/token correto quando API_KEY estiver configurada.
    Se nenhuma API_KEY for definida no servidor, o acesso opera em modo livre.
    """
    if not API_KEY:
        return True

    token = header_key or (bearer.credentials if bearer else None)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação necessária. Forneça o token via cabeçalho 'X-API-Key' ou 'Authorization: Bearer <token>'."
        )

    if not secrets.compare_digest(token.strip(), API_KEY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chave de autenticação inválida."
        )
    return True

TEMP_DIR = Path(tempfile.gettempdir()) / "autocutter_downloads"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


class DownloadRequest(BaseModel):
    url: str


def sanitize_filename(name: str) -> str:
    """Remove caracteres especiais e garante um nome de arquivo seguro."""
    name = unicodedata.normalize("NFKD", name)
    name = re.sub(r"[^\w\s\.-]", "", name).strip()
    name = re.sub(r"\s+", "_", name)
    return name[:80] or "video"


@app.get("/health")
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "Auto Cutter Downloader API",
        "auth_required": bool(API_KEY)
    }


@app.post("/api/info", dependencies=[Depends(verify_auth)])
def get_video_info(req: DownloadRequest):
    """Retorna metadados do vídeo (título, duração, thumbnail) sem baixar o arquivo."""
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL inválida ou vazia.")

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "windowsfilenames": True,
        "restrictfilenames": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["ios", "android"]
            }
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "title": info.get("title", "Vídeo"),
                "duration": info.get("duration", 0),
                "thumbnail": info.get("thumbnail"),
                "uploader": info.get("uploader"),
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao extrair dados do vídeo: {str(e)}")


@app.post("/api/download", dependencies=[Depends(verify_auth)])
def download_video(req: DownloadRequest):
    """
    Baixa o vídeo da URL fornecida (YouTube, TikTok, Instagram, etc.),
    garantindo compatibilidade com navegadores (H.264/AAC MP4) e retorna o arquivo.
    """
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Por favor, forneça uma URL válida.")

    # Cria diretório de trabalho temporário exclusivo para esta requisição
    work_dir = tempfile.mkdtemp(dir=TEMP_DIR)
    output_template = os.path.join(work_dir, "video.%(ext)s")

    ydl_opts = {
        "outtmpl": output_template,
        "windowsfilenames": True,
        "restrictfilenames": True,
        "nopart": True,
        "overwrites": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["ios", "android"]
            }
        },
        "format": "bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "postprocessors": [
            {
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4",
            }
        ],
        "postprocessor_args": {
            "merger": ["-movflags", "+faststart"],
        },
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        "noplaylist": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                raise ValueError("Nenhuma informação pôde ser obtida da URL.")

            title = info.get("title", "video")
            safe_title = sanitize_filename(title)
            final_filename = f"{safe_title}.mp4"

            # Localiza o arquivo baixado
            prepared = Path(ydl.prepare_filename(info))
            mp4_candidate = prepared.with_suffix(".mp4")

            file_path = None
            if mp4_candidate.exists():
                file_path = str(mp4_candidate)
            elif prepared.exists():
                file_path = str(prepared)
            else:
                files_in_dir = [f for f in Path(work_dir).iterdir() if f.is_file() and not f.name.endswith(".part")]
                if files_in_dir:
                    file_path = str(files_in_dir[0])

            if not file_path or not os.path.exists(file_path):
                raise FileNotFoundError("O arquivo de vídeo não foi encontrado após o download.")

            def cleanup():
                try:
                    shutil.rmtree(work_dir, ignore_errors=True)
                except Exception:
                    pass

            return FileResponse(
                path=file_path,
                media_type="video/mp4",
                filename=final_filename,
                headers={
                    "Content-Disposition": f'attachment; filename="{final_filename}"',
                    "Access-Control-Expose-Headers": "Content-Disposition",
                },
                background=BackgroundTask(cleanup),
            )

    except (yt_dlp.utils.DownloadError, yt_dlp.utils.YoutubeDLError) as de:
        try:
            os.rmdir(work_dir)
        except Exception:
            pass
        raise HTTPException(
            status_code=400,
            detail=f"Não foi possível baixar o vídeo desta URL. Verifique se o link está correto e público: {str(de)}",
        )
    except Exception as e:
        try:
            os.rmdir(work_dir)
        except Exception:
            pass
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao processar o download: {str(e)}",
        )
