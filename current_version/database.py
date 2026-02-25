from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

SQL_DB_URL = 'sqlite:///./my_database.db'

engine = create_engine(SQL_DB_URL)

session_local = sessionmaker( autoflush=False, autocommit=False, bind=engine)


# # Создаём базовый класс для моделей
Base = declarative_base()












































# class User(Base):
#     __tablename__ = 'users'

#     id = Column(Integer, primary_key=True, autoincrement=True)
#     nickname = Column(String, nullable=False, unique=True)
#     password = Column(String, nullable=False)
#     fullname = Column(String, nullable=False)
#     class_ = Column(Float, default=0.0)  # например, 10.1
#     project_id = Column(Integer, ForeignKey('projects.id'), nullable=True, default=None)
#     speciality = Column(String)
#     email = Column(String)
#     prof= Column(String)

#     # Связь с проектами, где пользователь является автором
#     authored_projects = relationship('Project', back_populates='author', foreign_keys='Project.author_id')
#     # Связь с проектом, в котором пользователь участвует (по project_id)
#     project = relationship('Project', foreign_keys=[project_id], back_populates='participants')
    
# class Project(Base):
#     __tablename__ = 'projects'

#     id = Column(Integer, primary_key=True, autoincrement=True)
#     title = Column(String, nullable=False)
#     body = Column(String, nullable=False)
#     underbody = Column(String, default='')
#     author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
#     tasks = Column(JSON, default=[])

#     # Связь с автором (один проект – один автор)
#     author = relationship('User', foreign_keys=[author_id], back_populates='authored_projects')
#     # Связь с участниками (по project_id в User)
#     participants = relationship('User', foreign_keys='User.project_id', back_populates='project')
    
# # Создаём движок (будет использоваться SQLite)
# engine = create_engine('sqlite:///my_database.db', echo=True)  # echo=True для отладки SQL-запросов

# # Создаём все таблицы, описанные в Base
# Base.metadata.create_all(engine)

# # Создаём фабрику сессий для последующей работы с данными
# Session = sessionmaker(bind=engine)
# session = Session()