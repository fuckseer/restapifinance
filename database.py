from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
import os
from dotenv import load_dotenv
load_dotenv(verbose=True)

DATABASE_URL = os.environ.get('DATABASE_URL')

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)