import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.models.db_models import PaymentDB
from app.api import payments, analytics, experiments, strategies, agent, demo, webhooks
from app.api.demo import seed_demo_environment
from app.api.payments import global_ml_model
from app.ml.generator import generate_synthetic_dataset

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("recoveriq.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing RecoverIQ Database...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Check if database is already populated
        payment_count = db.query(PaymentDB).count()
        if payment_count == 0:
            logger.info("Empty database detected. Seeding initial demo environment...")
            seed_demo_environment(db)
        else:
            logger.info(f"Existing RecoverIQ database detected with {payment_count} payments. Preserving state.")
            # Ensure in-memory ML model is trained
            if not global_ml_model.is_trained:
                logger.info("Training ML model on startup...")
                df_pre, df_post = generate_synthetic_dataset(n_samples=2000, seed=42)
                global_ml_model.train_and_evaluate(df_pre, df_post)
    except Exception as e:
        logger.error(f"Error during startup initialization: {e}")
    finally:
        db.close()
    yield
    logger.info("RecoverIQ Shutdown Complete.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="AI Revenue Recovery Decision Engine for Razorpay AI Builder Track 3",
    lifespan=lifespan
)

# Enable CORS for Vite frontend with explicit allowed origins
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "http://localhost:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Mount API Router
app.include_router(payments.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(experiments.router, prefix=settings.API_V1_STR)
app.include_router(strategies.router, prefix=settings.API_V1_STR)
app.include_router(agent.router, prefix=settings.API_V1_STR)
app.include_router(demo.router, prefix=settings.API_V1_STR)
app.include_router(webhooks.router, prefix=settings.API_V1_STR)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "model_version": settings.MODEL_VERSION,
        "policy_version": settings.POLICY_VERSION,
        "is_model_trained": global_ml_model.is_trained
    }

@app.get("/api/health/ready")
def health_ready():
    return {
        "status": "ready" if global_ml_model.is_trained else "initializing",
        "is_model_trained": global_ml_model.is_trained,
        "model_version": settings.MODEL_VERSION,
        "policy_version": settings.POLICY_VERSION
    }

