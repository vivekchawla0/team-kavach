import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

ACTIVE_DB_NAME = "Unknown"

def get_engine():
    global ACTIVE_DB_NAME
    db_url = settings.DATABASE_URL
    connect_args = {}
    
    # Direct SQLite requested
    if settings.DB_MODE.lower() == "sqlite" or db_url.startswith("sqlite"):
        ACTIVE_DB_NAME = "SQLite"
        connect_args["check_same_thread"] = False
        logger.info("=" * 60)
        logger.info("ACTIVE DATABASE: SQLite")
        logger.info("=" * 60)
        print("ACTIVE DATABASE: SQLite")
        return create_engine(db_url, connect_args=connect_args)
    
    # PostgreSQL Primary
    try:
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600
        )
        # Verify connection immediately
        with engine.connect() as conn:
            pass
        ACTIVE_DB_NAME = "PostgreSQL"
        logger.info("=" * 60)
        logger.info(f"ACTIVE DATABASE: PostgreSQL (Host: {settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}, DB: {settings.POSTGRES_DB})")
        logger.info("=" * 60)
        print(f"ACTIVE DATABASE: PostgreSQL (Host: {settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}, DB: {settings.POSTGRES_DB})")
        return engine
    except Exception as e:
        if not settings.ALLOW_SQLITE_FALLBACK:
            logger.critical(f"FATAL: Failed to connect to primary PostgreSQL database at {db_url} and ALLOW_SQLITE_FALLBACK is disabled. Error: {e}")
            raise RuntimeError(f"PostgreSQL connection failed: {e}")
        
        ACTIVE_DB_NAME = "SQLite Fallback"
        logger.warning("=" * 60)
        logger.warning(f"ACTIVE DATABASE: SQLite Fallback (PostgreSQL connection failed: {e})")
        logger.warning(f"Using local fallback database: {settings.SQLITE_FALLBACK_URL}")
        logger.warning("=" * 60)
        print(f"ACTIVE DATABASE: SQLite Fallback (PostgreSQL unavailable)")
        return create_engine(settings.SQLITE_FALLBACK_URL, connect_args={"check_same_thread": False})

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_active_database_info():
    return {
        "active_database": ACTIVE_DB_NAME,
        "dialect": engine.dialect.name,
        "is_postgresql": ACTIVE_DB_NAME == "PostgreSQL",
        "is_sqlite_fallback": "SQLite" in ACTIVE_DB_NAME,
        "postgres_server": settings.POSTGRES_SERVER,
        "postgres_port": settings.POSTGRES_PORT,
        "postgres_db": settings.POSTGRES_DB,
    }

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
