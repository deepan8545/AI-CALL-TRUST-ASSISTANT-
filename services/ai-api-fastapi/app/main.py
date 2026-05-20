import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers.calls import router
from app.modules.database import db
from app.modules.redis_reputation import redis_service
from app.modules.kafka_producer import kafka_producer
from app.modules.neo4j_graph import neo4j_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting AI Call Trust Assistant...")
    await db.connect()
    await redis_service.connect()
    await kafka_producer.connect()
    await neo4j_service.connect()
    yield
    # Shutdown
    logger.info("Shutting down...")
    await neo4j_service.disconnect()
    await kafka_producer.disconnect()
    await redis_service.disconnect()
    await db.disconnect()


app = FastAPI(
    title="AI Call Trust Assistant",
    description="Real-time trust engine for phone calls — scores, explains, and summarizes call risk.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router)
