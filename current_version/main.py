from fastapi import FastAPI, HTTPException, Query, Depends, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import or_, text
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from jose import JWTError, jwt
import uvicorn
import os
import io
import uuid
import random
import string
from dotenv import load_dotenv

load_dotenv()

from models import Base, User, Project
from database import engine, session_local
from schemas import (

    UserResponse, UserCreate, UserUpdate, LoginRequest,

    TeacherCreate, TeacherResponse,

    ProjectResponse, ProjectCreate, ProjectUpdate,

    Comment,

    EmailVerificationCodeRequest, EmailVerificationRequest,
    PasswordResetRequest, PasswordResetConfirm,

    TokenResponse
)

from willow import Image
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

# Импорты из auth.py
from auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    get_current_user,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    oauth2_scheme
)

from email_utils import generate_verification_code, send_verification_email, send_password_reset_email
from core.memory_store import memory_store as redis_client

app = FastAPI()

# Настройка CORS
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
    expose_headers=["*"],
    max_age=3600,
)

os.makedirs("avatars", exist_ok=True)
app.mount("/avatars", StaticFiles(directory="avatars"), name="avatars")
AVATAR_DIR = "avatars" 

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

@app.get("/users/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Получение информации о текущем пользователе по JWT токену
    """
    return current_user

@app.post("/users/", response_model=UserResponse, summary="Создать юзера", tags=["USERDB"])
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Проверка уникальности
    existing_nickname = db.query(User).filter(User.nickname == user.nickname.strip()).first()
    if existing_nickname:
        raise HTTPException(
            status_code=400, 
            detail="Пользователь с таким никнеймом уже существует"
        )
    
    existing_email = db.query(User).filter(User.email == user.email.strip()).first()
    if existing_email:
        raise HTTPException(
            status_code=400, 
            detail="Пользователь с таким email уже существует"
        )
    
    # Хешируем пароль
    hashed_password = get_password_hash(user.password.strip())
    
    db_user = User(
        nickname=user.nickname.strip(),
        fullname=user.fullname,
        class_=user.class_,
        speciality=user.speciality,
        email=user.email.strip(),
        password=hashed_password,
        avatar=None,
        is_active=True,      
        is_verified=False      
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
    q: Optional[str] = Query(None, description="Поисковый запрос"),
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
    users = db.query(User).all()
    for user in users:
        if user.avatar:
            filepath = os.path.join(AVATAR_DIR, user.avatar)
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except OSError as e:
                    print(f"Ошибка при удалении файла {filepath}: {e}")
    
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
        filepath = os.path.join(AVATAR_DIR, user.avatar)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError as e:
                print(f"Ошибка при удалении файла {filepath}: {e}")
    
    all_projects = db.query(Project).all()
    for project in all_projects:
        if user_id in (project.authors_ids or []):
            authors = list(project.authors_ids)
            authors.remove(user_id)
            project.authors_ids = authors
    
    db.delete(user)
    db.commit()
    return {"message": f"User {user_id} deleted successfully"}

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
        tasks=project.tasks,
        links=project.links
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@app.get("/projects/", response_model=List[ProjectResponse], summary="Список проектов", tags=["PROJECTDB"])
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
    if project_update.links is not None:
        project.links = project_update.links
    if project_update.comments is not None: 
        project.comments = [comment.dict() for comment in project_update.comments]  # Конвертируем Pydantic модели в словари

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

@app.get("/search", response_model=List[ProjectResponse], summary="Поиск проектов", tags=["PROJECTDB"])
async def search_projects(
    q: Optional[str] = Query(None, description="Строка для поиска по названию"),
    db: Session = Depends(get_db)
):
    if not q:
        return []
    projects = db.query(Project).filter(Project.title.ilike(f"%{q}%")).all()
    return projects

@app.delete("/projects/", summary="Удалить проекты", tags=["PROJECTDB"])
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

@app.post("/auth/request-verification-code")
async def request_verification_code(
    request: EmailVerificationCodeRequest,
    db: Session = Depends(get_db)
):
    """
    Запрашивает код подтверждения на указанный email (для новых пользователей)
    """
    # Проверяем, не занят ли email
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Генерируем код и сохраняем на 10 минут
    code = generate_verification_code()
    redis_client.setex(f"verify:{request.email}", 600, code)
    
    # Отправляем код по email
    await send_verification_email(request.email, code)
    
    return {"message": "Verification code sent"}

@app.post("/auth/request-verification")
async def request_verification(
    request: EmailVerificationCodeRequest,
    db: Session = Depends(get_db)
):
    """
    Запрашивает код подтверждения для уже существующего пользователя
    (для повторной отправки из профиля)
    """
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_verified:
        raise HTTPException(status_code=400, detail="Email already verified")
    
    # Генерируем код и сохраняем на 10 минут
    code = generate_verification_code()
    redis_client.setex(f"verify:{request.email}", 600, code)
    
    # Отправляем код по email
    await send_verification_email(request.email, code)
    
    return {"message": "Verification code sent"}

@app.post("/auth/verify-email")
async def verify_email(
    request: dict,
    db: Session = Depends(get_db)
):
    """
    Подтверждает email пользователя по коду
    """
    email = request.get("email")
    code = request.get("code")
    
    if not email or not code:
        raise HTTPException(status_code=400, detail="Email and code required")
    
    # Проверяем код
    stored_code = redis_client.get(f"verify:{email}")
    if not stored_code or stored_code != code:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    
    # Удаляем использованный код
    redis_client.delete(f"verify:{email}")
    
    # Находим пользователя и подтверждаем email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_verified = True
    db.commit()
    db.refresh(user)
    
    return {"message": "Email successfully verified", "user": user}

@app.post("/auth/register-with-verification", response_model=UserResponse)
async def register_with_verification(
    request: dict,
    db: Session = Depends(get_db)
):
    """
    Регистрация нового пользователя с проверкой кода подтверждения
    """
    email = request.get("email")
    code = request.get("code")
    user_data = request.get("user_data")
    
    if not email or not code or not user_data:
        raise HTTPException(status_code=400, detail="Email, code and user data required")
    
    stored_code = redis_client.get(f"verify:{email}")
    if not stored_code or stored_code != code:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")
    
    redis_client.delete(f"verify:{email}")
    
    existing_user = db.query(User).filter(
        (User.nickname == user_data.get('nickname')) | 
        (User.email == email)
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Nickname or email already registered")
    
    hashed_password = get_password_hash(user_data.get('password'))
    
    db_user = User(
        nickname=user_data.get('nickname').strip(),
        fullname=user_data.get('fullname'),
        class_=user_data.get('class_', 0),
        speciality=user_data.get('speciality'),
        email=email,
        password=hashed_password,
        avatar=None,
        is_verified=True,   # Сразу подтверждаем, т.к. код проверен
        is_active=True
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/auth/login", response_model=TokenResponse)
async def auth_login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Вход в систему, возвращает access и refresh токены
    """
    user = db.query(User).filter(
        (User.nickname == credentials.nickname.strip()) | 
        (User.email == credentials.nickname.strip())
    ).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Проверка пароля через bcrypt
    if not verify_password(credentials.password.strip(), user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Не проверяем is_verified - пускаем всех активных пользователей
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")
    
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    redis_client.setex(
        f"refresh:{user.id}:{refresh_token}",
        REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        "valid"
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )