from .config import settings
from sqlalchemy import  create_engine, sessionmaker 
from sqlalchemy.orm import declarative_base



engine = create_engine(
    settings.DATABASE_URL,
    echo=True, 
    pool_pre_ping=True,

)


Base = declarative_base()


session_local = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

def db_session():
    return session_local()
