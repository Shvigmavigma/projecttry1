from fastapi import FastAPI, HTTPException, Query, Depends, File, UploadFile
import uvicorn
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_, text
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from models import Base, User, Project
from database import engine, session_local
from schemas import (
    UserResponse, UserCreate,
    ProjectResponse, ProjectCreate, ProjectUpdate,
    TeacherCreate, TeacherResponse, LoginRequest, UserUpdate
)
from willow import Image
import os
from fastapi.staticfiles import StaticFiles
import uuid
import os
from io import BytesIO
import io
from willow import Image
import uuid

app = FastAPI()

origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",   
    "http://127.0.0.1:5174",     
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
os.makedirs("avatars", exist_ok=True)
app.mount("/avatars", StaticFiles(directory="avatars"), name="avatars")
AVATAR_DIR = "avatars" 

def delete_avatar_file(avatar_filename: str):
    """Удаляет файл аватарки, если он существует."""
    if not avatar_filename:
        return
    filepath = os.path.join(AVATAR_DIR, avatar_filename)
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except OSError as e:
            print(f"Ошибка при удалении файла {filepath}: {e}")

Base.metadata.create_all(bind=engine)

def get_db():
    db = session_local()
    try:
        yield db
    finally:
        db.close()

# ---------- USERS ----------

@app.put("/users/{user_id}", response_model=UserResponse, tags=["USERDB"])
async def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_update.fullname is not None:
        user.fullname = user_update.fullname
    if user_update.email is not None:
        user.email = user_update.email
    if user_update.class_ is not None:
        user.class_ = user_update.class_
    if user_update.speciality is not None:
        user.speciality = user_update.speciality

    db.commit()
    db.refresh(user)
    return user


@app.post("/login", response_model=UserResponse, tags=["USERDB"])
async def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        (User.nickname == credentials.nickname.strip()) | (User.email == credentials.nickname.strip())
    ).first()
    if not user or user.password != credentials.password.strip():
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    return user


@app.post("/users/", response_model=UserResponse, summary="Создать юзера", tags=["USERDB"])
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(
        nickname=user.nickname.strip(),
        fullname=user.fullname,
        class_=user.class_,
        speciality=user.speciality,
        email=user.email.strip(),
        password=user.password.strip()  
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/userslist/", response_model=List[UserResponse], summary="Список юзеров", tags=["USERDB"])
async def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@app.get("/users/", response_model=List[UserResponse], summary="Поиск пользователей", tags=["USERDB"])
async def search_users(
    q: Optional[str] = Query(None, description="Поисковый запрос (никнейм, имя, email или ID)"),
    db: Session = Depends(get_db)
):
    query = db.query(User)
    if q:
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


@app.delete("/users/all", summary="Удалить всех пользователей", tags=["USERDB"])
async def delete_all_users(db: Session = Depends(get_db)):
    """
    Удаляет всех пользователей и все связанные с ними аватарки.
    Перед удалением во всех проектах поле authors_ids принудительно устанавливается в пустой массив '[]'.
    """
    users = db.query(User).all()
    for user in users:
        if user.avatar:
            delete_avatar_file(user.avatar)
    db.execute(text("UPDATE projects SET authors_ids = '[]'"))

    deleted_count = db.query(User).delete()
    db.commit()

    return {"message": f"Удалено пользователей: {deleted_count}"}

@app.delete("/users/{user_id}", summary="Удалить пользователя по ID", tags=["USERDB"])
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.avatar:
        delete_avatar_file(user.avatar)
    all_projects = db.query(Project).all()
    for project in all_projects:
        if user_id in (project.authors_ids or []):
            authors = list(project.authors_ids)
            authors.remove(user_id)
            project.authors_ids = authors
    db.delete(user)
    db.commit()

    return {"message": f"User {user_id} deleted successfully and removed from projects authors"}

@app.post("/users/{user_id}/avatar", response_model=UserResponse, tags=["USERDB"])
async def upload_avatar(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5 MB)")

    try:
        img = Image.open(io.BytesIO(contents))

        width, height = img.get_size()
        crop_size = min(width, height)
        left = (width - crop_size) // 2
        top = (height - crop_size) // 2
        right = left + crop_size
        bottom = top + crop_size
        img = img.crop((left, top, right, bottom))

        img = img.resize((256, 256))

        unique_id = uuid.uuid4().hex[:8]
        filename = f"user_{user_id}_{unique_id}.webp"
        filepath = os.path.join("avatars", filename)

        # Сохраняем через Willow, передавая путь к файлу
        img.save_as_webp(filepath)

        if user.avatar:
            old_path = os.path.join("avatars", user.avatar)
            if os.path.exists(old_path):
                os.remove(old_path)

        user.avatar = filename
        db.commit()
        db.refresh(user)

        return user

    except Exception as e:
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)
        raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")
# ---------- PROJECTS ----------
@app.post("/projects/", response_model=ProjectResponse, summary="Создать проект", tags=["PROJECTDB"])
async def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    author = db.query(User).filter(User.id == project.authors_ids[0]).first()
    if not author:
        raise HTTPException(status_code=404, detail=f"Автор с ID {project.authors_ids[0]} не найден")
    db_project = Project(
        title=project.title,
        body=project.body,
        underbody=project.underbody,
        authors_ids=[project.authors_ids[0]],   
        tasks=project.tasks
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@app.get("/projects/", response_model=List[ProjectResponse], summary="Список проектов (с фильтром по автору)", tags=["PROJECTDB"])
async def get_projects(
    author_id: Optional[int] = Query(None, description="ID автора для фильтрации проектов"),
    db: Session = Depends(get_db)
):
    if author_id is not None:
        
        all_projects = db.query(Project).all()
        projects = [p for p in all_projects if author_id in (p.authors_ids or [])]
    else:
        projects = db.query(Project).all()
    return projects

@app.get("/projects/{project_id}", response_model=ProjectResponse, summary="Конкретный проект", tags=["PROJECTDB"])
async def get_project_by_id(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@app.put("/projects/{project_id}", response_model=ProjectResponse, summary="Обновление проекта", tags=["PROJECTDB"])
async def update_project(project_id: int, project_update: ProjectUpdate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project_update.title is not None:
        project.title = project_update.title
    if project_update.body is not None:
        project.body = project_update.body
    if project_update.underbody is not None:
        project.underbody = project_update.underbody
    if project_update.tasks is not None:
        project.tasks = project_update.tasks

    if project_update.authors_ids is not None:
        users = db.query(User).filter(User.id.in_(project_update.authors_ids)).all()
        if len(users) != len(project_update.authors_ids):
            raise HTTPException(status_code=404, detail="Один или несколько авторов не найдены")
        project.authors_ids = project_update.authors_ids
    elif project_update.author_id is not None:
        author = db.query(User).filter(User.id == project_update.author_id).first()
        if not author:
            raise HTTPException(status_code=404, detail=f"Автор с ID {project_update.author_id} не найден")
        if project.authors_ids is None:
            project.authors_ids = []
        if project_update.author_id not in project.authors_ids:
            project.authors_ids = list(project.authors_ids) + [project_update.author_id]

    db.commit()
    db.refresh(project)
    return project
@app.get("/search", response_model=List[ProjectResponse], summary="Поиск проектов по названию", tags=["PROJECTDB"])
async def search_projects(
    q: Optional[str] = Query(None, description="Строка для поиска по названию (частичное совпадение)"),
    db: Session = Depends(get_db)
):
    if not q:
        return []
    projects = db.query(Project).filter(Project.title.ilike(f"%{q}%")).all()
    return projects

@app.delete("/projects/", summary="Удалить проекты (все или один)", tags=["PROJECTDB"])
async def delete_projects(
    project_id: Optional[int] = None,
    all: bool = Query(False, description="Удалить все проекты"),
    db: Session = Depends(get_db)
):
    if all:
        count = db.query(Project).delete()
        db.commit()
        return {"message": f"Удалено проектов: {count}"}
    elif project_id is not None:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        db.delete(project)
        db.commit()
        return {"message": f"Project {project_id} deleted"}
    else:
        raise HTTPException(status_code=400, detail="Specify project_id or all=true")
