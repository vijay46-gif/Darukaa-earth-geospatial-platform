import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.utils.config import settings

logger = logging.getLogger("darukaa.database")
logging.basicConfig(level=logging.INFO)

Base = declarative_base()


def get_engine():
    primary_url = settings.DATABASE_URL
    is_postgres = primary_url.startswith("postgresql")

    if is_postgres:
        try:
            engine = create_engine(primary_url, pool_pre_ping=True, pool_size=10, max_overflow=20)
            # Test connectivity
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                # Try enabling postgis if superuser or available
                try:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
                    conn.commit()
                    logger.info("Connected to PostgreSQL with PostGIS extension enabled.")
                except Exception as ext_err:
                    logger.warning(f"PostGIS extension check note: {ext_err}")
            return engine, True
        except Exception as e:
            logger.warning(
                f"PostgreSQL connection to {primary_url} failed ({e}). "
                f"Falling back to local SQLite engine ({settings.SQLITE_FALLBACK_URL}) for seamless local development."
            )

    # SQLite fallback
    engine = create_engine(settings.SQLITE_FALLBACK_URL, connect_args={"check_same_thread": False})
    logger.info(f"Connected to local SQLite engine: {settings.SQLITE_FALLBACK_URL}")
    return engine, False


engine, IS_POSTGRES = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
