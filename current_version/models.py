from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nickname = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    fullname = Column(String, nullable=False, index=True)
    class_ = Column(Float, default=0.0)
    speciality = Column(String, nullable=True)
    email = Column(String, nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)

    authored_projects = relationship(
        "Project",
        back_populates="author",
        foreign_keys="Project.author_id"
    )

    project = relationship(
        "Project",
        back_populates="participants",
        foreign_keys="User.project_id"
    )


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    body = Column(String, nullable=False)
    underbody = Column(String, default="")
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    tasks = Column(JSON, default=[])

    author = relationship(
        "User",
        back_populates="authored_projects",
        foreign_keys="Project.author_id"
    )

    participants = relationship(
        "User",
        back_populates="project",
        foreign_keys="User.project_id"
    )
    
