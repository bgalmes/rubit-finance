import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

from rubit.api.routers import mortgages
from rubit.domain import MortgageValidationError
from rubit.persistence import create_db_engine, default_db_path

WEB_DIR_ENV = "RUBIT_WEB_DIR"
PACKAGED_WEB_DIR = Path(__file__).resolve().parents[1] / "static"
REPO_WEB_DIR = Path(__file__).resolve().parents[4] / "web" / ".output" / "public"


def find_web_dir() -> Path | None:
    """The built SPA: ``$RUBIT_WEB_DIR``, then the packaged copy, then the repo build."""
    env_dir = os.environ.get(WEB_DIR_ENV)
    candidates = [Path(env_dir)] if env_dir else [PACKAGED_WEB_DIR, REPO_WEB_DIR]
    return next((path for path in candidates if (path / "index.html").is_file()), None)


@dataclass(frozen=True)
class Settings:
    db_path: Path = field(default_factory=default_db_path)
    web_dir: Path | None = field(default_factory=find_web_dir)


class SPAStaticFiles(StaticFiles):
    """Serves the SPA's files, and ``index.html`` for anything else (client-side routes).

    ``html`` mode stays off: it would serve Nuxt's ``404.html`` with a 404 status and
    redirect generated route folders (``/compare`` → ``/compare/``).
    """

    def __init__(self, directory: Path) -> None:
        super().__init__(directory=directory, html=False)

    async def get_response(self, path: str, scope: Scope) -> Response:
        if path.split("/", 1)[0] == "api":
            # Unknown API paths get FastAPI's JSON 404, not the SPA.
            raise StarletteHTTPException(status.HTTP_404_NOT_FOUND)
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code != status.HTTP_404_NOT_FOUND:
                raise
            return await super().get_response("index.html", scope)


async def validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, MortgageValidationError)
    detail = [
        {"type": "value_error", "loc": ["body", exc.field_name], "msg": exc.message},
    ]
    return JSONResponse({"detail": detail}, status_code=status.HTTP_422_UNPROCESSABLE_CONTENT)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        app.state.engine = create_db_engine(settings.db_path)
        yield
        app.state.engine.dispose()

    app = FastAPI(title="Rubit Finance", version="0.1.0", lifespan=lifespan)
    app.add_exception_handler(MortgageValidationError, validation_error_handler)
    app.include_router(mortgages.router)
    if settings.web_dir is not None:
        app.mount("/", SPAStaticFiles(settings.web_dir), name="web")
    return app


app = create_app()
