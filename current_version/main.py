from fastapi import FastAPI, HTTPException, Path, Query, Body, Depends
import uvicorn
from typing import Optional, List, Dict, Annotated
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from fastapi.middleware.cors import CORSMiddleware

from models import Base, User, Project
from database import engine, session_local
from schemas import UserResponse, UserCreate, ProjectCreate, ProjectResponse, TeacherCreate, TeacherResponse



app = FastAPI()


origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)




def get_db():
    db = session_local()
    try:
        yield db
    finally:
        db.close()

#USERS

@app.post(path="/users/", response_model=UserResponse,  summary="Создать юзера", tags=["USERDB"])
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(
    nickname=user.nickname,
    fullname=user.fullname,
    class_=user.class_,
    speciality=user.speciality,
    email=user.email,
    project_id=user.project_id,
    password=user.password 
)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
@app.get(path="/userslist/", response_model=List[UserResponse], summary="список юзеров", tags=["USERDB"])
async def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users


@app.get("/users/", response_model=List[UserResponse], summary="Поиск пользователей", tags=["USERDB"])
async def search_users(
    q: Optional[str] = Query(None, description="Поисковый запрос (никнейм, имя, email или ID)"),
    db: Session = Depends(get_db)
):
    """
    Выполняет поиск пользователей по:
    - никнейму (частичное совпадение, без учёта регистра)
    - полному имени (частичное совпадение)
    - email (частичное совпадение)
    - ID (если запрос является числом, ищет точное совпадение)
    
    Если `q` не указан, возвращает всех пользователей.
    """
    query = db.query(User)
    
    if q:
        # Пытаемся преобразовать q в число для поиска по ID
        try:
            user_id = int(q)
            id_filter = (User.id == user_id)
        except ValueError:
            id_filter = None 
        
        text_filters = [
            User.nickname.ilike(f"%{q}%"),
            User.fullname.ilike(f"%{q}%"),
            User.email.ilike(f"%{q}%")
        ]
        
        if id_filter is not None:
            query = query.filter(or_(id_filter, *text_filters))
        else:
            query = query.filter(or_(*text_filters))
    
    users = query.all()
    return users

@app.delete(path="/users/{user_id}", summary="Удалить пользователя по ID", tags=["USERDB"])
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return {"message": f"User {user_id} deleted successfully"}

#PROJECTS


@app.post(path="/projects/", response_model=ProjectResponse,  summary="создать проект", tags=["PROJECTDB"])
async def create_post(post: ProjectCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == post.author_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail='User not found')
    
    db_post = Project(
    title=post.title,
    body=post.body,
    underbody=post.underbody,
    author_id=post.author_id,
    tasks=post.tasks            
)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

@app.get(path="/projects/", response_model=List[ProjectResponse],  summary="список проектов", tags=["PROJECTDB"])
async def get_posts(db: Session = Depends(get_db)):
    posts = db.query(Project).options(joinedload(Project.author)).all()
    return posts

@app.get(path="/projects/{project_id}", response_model=ProjectResponse,  summary="конкретный проект", tags=["PROJECTDB"])
async def get_post_by_id(project_id: int, db: Session = Depends(get_db)):
    post = db.query(Project).options(joinedload(Project.author)).filter(Project.id == project_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@app.put(path="/projects/{project_id}", response_model=ProjectResponse,   summary="обновление проекта", tags=["PROJECTDB"])
async def update_project(project_id: int, project_update: ProjectCreate, db: Session = Depends(get_db)):
    # Ищем проект по ID
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    

    author = db.query(User).filter(User.id == project_update.author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    

    project.title = project_update.title
    project.body = project_update.body
    project.underbody = project_update.underbody  
    project.author_id = project_update.author_id
    project.tasks = project_update.tasks         
    
    db.commit()
    db.refresh(project)
    return project

@app.delete(path="/projects/{project_id}", summary="удалить проект по ID проект", tags=["PROJECTDB"])
async def delete_project(project_id: int, db: Session = Depends(get_db)):
    # Ищем проект по ID
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db.delete(project)
    db.commit()
    return {"message": f"Project {project_id} deleted successfully"}

@app.get("/search", response_model=List[ProjectResponse], summary="Поиск проектов по названию", tags=["PROJECTDB"])
async def search_projects(
    q: Optional[str] = Query(None, description="Строка для поиска по названию (частичное совпадение)"),
    db: Session = Depends(get_db)
):
    """
    Выполняет поиск проектов по названию (title) с использованием частичного совпадения без учёта регистра.
    - Если передан параметр `q`, возвращает список проектов, название которых содержит эту строку.
    - Если `q` не передан или пустой, возвращает пустой список.
    - Для каждого проекта подгружается информация об авторе (поле `author`).
    """
    if not q:
        return []
    
    projects = (
        db.query(Project)
        .options(joinedload(Project.author))
        .filter(Project.title.ilike(f"%{q}%"))
        .all()
    )
    return projects

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)