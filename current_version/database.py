from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

SQL_DB_URL = 'sqlite:///./my_database.db'

engine = create_engine(SQL_DB_URL)

session_local = sessionmaker( autoflush=False, autocommit=False, bind=engine)


# # Создаём базовый класс для моделей
Base = declarative_base()


