from sqlalchemy import Column, Integer, String, Float, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)          # хранится хеш
    fullname = Column(String, nullable=False, index=True)
    class_ = Column(Float, default=0.0)
    speciality = Column(String, nullable=True)
    email = Column(String, nullable=False, index=True)


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    body = Column(String, nullable=False)
    underbody = Column(String, default="")
    authors_ids = Column(JSON, nullable=False, default=list)  # список ID авторов
    tasks = Column(JSON, default=list)