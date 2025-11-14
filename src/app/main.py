from fastapi import FastAPI
import psycopg2
from datetime import datetime

from app.application.waste_controller import router as waste_router
from app.config.settings import settings
from app.config.cors_config import setup_cors


def create_app() -> FastAPI:
    app = FastAPI(
        title="Waste Management API",
        version="1.0.0",
        description="API para registro de residuos y análisis con Azure OpenAI",
        swagger_ui_parameters={"persistAuthorization": True},
        docs_url="/waste-api/docs",
        redoc_url="/waste-api/redoc",
        openapi_url="/waste-api/openapi.json",
        openapi_tags=[
            {"name": "Health", "description": "Health check del servicio"},
            {"name": "Waste", "description": "Gestión de residuos y análisis IA"},
        ],
    )

    # -------------------------------------------------------------
    # CORS
    # -------------------------------------------------------------
    setup_cors(app)

    # -------------------------------------------------------------
    # Health Check
    # -------------------------------------------------------------
    @app.get("/waste-api/health", tags=["Health"])
    async def health_check():
        """
        Verifica la conexión a PostgreSQL y estado del API.
        """
        try:
            conn = psycopg2.connect(
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT,
                database=settings.POSTGRES_DB,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
            )
            conn.close()

            return {
                "status": "healthy",
                "service": "waste-api",
                "version": "1.0.0",
                "database": "connected",
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "waste-api",
                "version": "1.0.0",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    # -------------------------------------------------------------
    # Routers del sistema
    # -------------------------------------------------------------
    app.include_router(
        waste_router,
        prefix="/waste-api",
        tags=["Waste"],
    )

    return app


app = create_app()
