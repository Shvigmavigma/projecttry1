from fastapi import FastAPI, HTTPException, Query, Depends, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import or_, text, and_
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
import json
from pathlib import Path

load_dotenv()

from models import Base, User, Project
from database import engine, session_local
from schemas import (
    # Student schemas
    StudentCreate, StudentResponse, StudentUpdate,
    # Teacher schemas
    TeacherCreate, TeacherResponse, TeacherUpdate, TeacherInfo,
    # Common schemas
    UserResponse, LoginRequest,
    # Project schemas
    ProjectResponse, ProjectCreate, ProjectUpdate, Comment,
    # Email schemas
    EmailVerificationCodeRequest, EmailVerificationRequest,
    PasswordResetRequest, PasswordResetConfirm,
    # Token schemas
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

app = FastAPI(title="School Platform API", description="API для управления учениками, учителями и проектами")

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

# Создаем директории
os.makedirs("avatars", exist_ok=True)
app.mount("/avatars", StaticFiles(directory="avatars"), name="avatars")
AVATAR_DIR = "avatars" 

# Создаем таблицы
Base.metadata.create_all(bind=engine)

def get_db():
    db = session_local()
    try:
        yield db
    finally:
        db.close()

# ==================== TEACHER EMAIL VERIFICATION ====================

ACCEPTED_EMAILS_FILE = Path("accepted_emails.json")

def load_accepted_emails():
    """
    Загружает список разрешенных email из файла
    """
    if not ACCEPTED_EMAILS_FILE.exists():
        # Создаем файл с примером, если его нет
        example_emails = {
            "accepted_emails": [
                "teacher@school.ru",
                "professor@university.ru",
                "учитель@школа.рф"
            ],
            "domains": [
                "school.ru",
                "education.ru",
                "teacher.org"
            ]
        }
        with open(ACCEPTED_EMAILS_FILE, 'w', encoding='utf-8') as f:
            json.dump(example_emails, f, ensure_ascii=False, indent=2)
        return example_emails
    
    try:
        with open(ACCEPTED_EMAILS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка загрузки файла с email: {e}")
        return {"accepted_emails": [], "domains": []}

def is_email_accepted(email: str) -> bool:
    """
    Проверяет, разрешен ли email для регистрации учителя
    """
    data = load_accepted_emails()
    email_lower = email.lower()
    
    # Проверка по конкретным email
    if email_lower in [e.lower() for e in data.get("accepted_emails", [])]:
        return True
    
    # Проверка по доменам
    domain = email_lower.split('@')[-1]
    if domain in [d.lower() for d in data.get("domains", [])]:
        return True
    
    return False

# ==================== STUDENTS ====================

@app.post("/students/", response_model=StudentResponse, summary="Создать ученика", tags=["Students"])
async def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    """
    Регистрация нового ученика
    """
    # Проверка уникальности
    existing_nickname = db.query(User).filter(User.nickname == student.nickname.strip()).first()
    if existing_nickname:
        raise HTTPException(
            status_code=400, 
            detail="Пользователь с таким никнеймом уже существует"
        )
    
    existing_email = db.query(User).filter(User.email == student.email.strip()).first()
    if existing_email:
        raise HTTPException(
            status_code=400, 
            detail="Пользователь с таким email уже существует"
        )
    
    # Хешируем пароль
    hashed_password = get_password_hash(student.password.strip())
    
    db_user = User(
        nickname=student.nickname.strip(),
        fullname=student.fullname,
        class_=student.class_,
        speciality=student.speciality,
        email=student.email.strip(),
        password=hashed_password,
        avatar=None,
        is_active=True,
        is_verified=False,  # Ученики могут быть без подтверждения
        is_teacher=False,
        teacher_info=None
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/students/", response_model=List[StudentResponse], summary="Список всех учеников", tags=["Students"])
async def get_students(
    q: Optional[str] = Query(None, description="Поиск по имени или никнейму"),
    db: Session = Depends(get_db)
):
    """
    Получить список всех учеников с возможностью поиска
    """
    query = db.query(User).filter(User.is_teacher == False)
    
    if q:
        query = query.filter(
            or_(
                User.nickname.ilike(f"%{q}%"),
                User.fullname.ilike(f"%{q}%"),
                User.email.ilike(f"%{q}%")
            )
        )
    
    students = query.all()
    return students

@app.get("/students/{student_id}", response_model=StudentResponse, summary="Получить ученика по ID", tags=["Students"])
async def get_student(student_id: int, db: Session = Depends(get_db)):
    """
    Получить информацию об ученике по его ID
    """
    student = db.query(User).filter(User.id == student_id, User.is_teacher == False).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@app.put("/students/{student_id}", response_model=StudentResponse, summary="Обновить ученика", tags=["Students"])
async def update_student(
    student_id: int, 
    student_update: StudentUpdate, 
    db: Session = Depends(get_db)
):
    """
    Обновить информацию об ученике
    """
    student = db.query(User).filter(User.id == student_id, User.is_teacher == False).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if student_update.fullname is not None:
        student.fullname = student_update.fullname
    if student_update.email is not None:
        # Проверяем уникальность email
        existing = db.query(User).filter(User.email == student_update.email, User.id != student_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        student.email = student_update.email
    if student_update.class_ is not None:
        student.class_ = student_update.class_
    if student_update.speciality is not None:
        student.speciality = student_update.speciality

    db.commit()
    db.refresh(student)
    return student

@app.delete("/students/{student_id}", summary="Удалить ученика", tags=["Students"])
async def delete_student(student_id: int, db: Session = Depends(get_db)):
    """
    Удалить ученика по ID
    """
    student = db.query(User).filter(User.id == student_id, User.is_teacher == False).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Удаляем аватар
    if student.avatar:
        filepath = os.path.join(AVATAR_DIR, student.avatar)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError as e:
                print(f"Ошибка при удалении файла {filepath}: {e}")
    
    # Удаляем из проектов
    all_projects = db.query(Project).all()
    for project in all_projects:
        if student_id in (project.authors_ids or []):
            authors = list(project.authors_ids)
            authors.remove(student_id)
            project.authors_ids = authors
    
    db.delete(student)
    db.commit()
    return {"message": f"Student {student_id} deleted successfully"}

# ==================== TEACHERS ====================

@app.post("/auth/check-teacher-email", tags=["Auth"])
async def check_teacher_email(request: dict):
    """
    Проверяет, разрешен ли email для регистрации учителя
    """
    email = request.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    if is_email_accepted(email):
        return {"accepted": True, "message": "Email разрешен для регистрации учителя"}
    else:
        raise HTTPException(
            status_code=403, 
            detail="Этот email не разрешен для регистрации учителя. Используйте email из списка разрешенных."
        )

@app.post("/teachers/", response_model=TeacherResponse, summary="Создать учителя", tags=["Teachers"])
async def create_teacher(teacher: TeacherCreate, db: Session = Depends(get_db)):
    """
    Регистрация нового учителя с проверкой email
    """
    # Проверка, разрешен ли email
    if not is_email_accepted(teacher.email):
        raise HTTPException(
            status_code=403,
            detail="Этот email не разрешен для регистрации учителя. Используйте email из списка разрешенных."
        )
    
    # Проверка уникальности
    existing_nickname = db.query(User).filter(User.nickname == teacher.nickname.strip()).first()
    if existing_nickname:
        raise HTTPException(
            status_code=400, 
            detail="Пользователь с таким никнеймом уже существует"
        )
    
    existing_email = db.query(User).filter(User.email == teacher.email.strip()).first()
    if existing_email:
        raise HTTPException(
            status_code=400, 
            detail="Пользователь с таким email уже существует"
        )
    
    # Хешируем пароль
    hashed_password = get_password_hash(teacher.password.strip())
    
    # Преобразуем TeacherInfo в словарь
    teacher_info_dict = teacher.teacher_info.dict() if teacher.teacher_info else {}
    
    db_user = User(
        nickname=teacher.nickname.strip(),
        fullname=teacher.fullname,
        class_=None,  # У учителя нет класса
        speciality=teacher.speciality,
        email=teacher.email.strip(),
        password=hashed_password,
        avatar=None,
        is_active=True,
        is_verified=False,  # Будет подтвержден после верификации email
        is_teacher=True,
        teacher_info=teacher_info_dict
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Отправляем код подтверждения на email
    code = generate_verification_code()
    redis_client.setex(f"verify:{teacher.email}", 600, code)
    await send_verification_email(teacher.email, code)
    
    return db_user

@app.post("/teachers/verify-and-create", response_model=TeacherResponse, tags=["Teachers"])
async def verify_and_create_teacher(
    request: dict,
    db: Session = Depends(get_db)
):
    """
    Завершает регистрацию учителя после подтверждения email
    (используется после ввода кода из email)
    """
    email = request.get("email")
    code = request.get("code")
    teacher_data = request.get("teacher_data")
    
    if not email or not code or not teacher_data:
        raise HTTPException(status_code=400, detail="Email, code and teacher data required")
    
    # Проверяем код
    stored_code = redis_client.get(f"verify:{email}")
    if not stored_code or stored_code != code:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")
    
    # Удаляем использованный код
    redis_client.delete(f"verify:{email}")
    
    # Проверяем, разрешен ли email
    if not is_email_accepted(email):
        raise HTTPException(
            status_code=403,
            detail="Этот email не разрешен для регистрации учителя"
        )
    
    # Проверяем, не зарегистрирован ли уже пользователь
    existing_user = db.query(User).filter(
        (User.nickname == teacher_data.get('nickname')) | 
        (User.email == email)
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Nickname or email already registered")
    
    # Хешируем пароль
    hashed_password = get_password_hash(teacher_data.get('password'))
    
    # Создаем учителя
    db_user = User(
        nickname=teacher_data.get('nickname').strip(),
        fullname=teacher_data.get('fullname'),
        class_=None,
        speciality=teacher_data.get('speciality'),
        email=email,
        password=hashed_password,
        avatar=None,
        is_verified=True,  # Сразу подтверждаем, т.к. код проверен
        is_active=True,
        is_teacher=True,
        teacher_info=teacher_data.get('teacher_info', {})
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/teachers/", response_model=List[TeacherResponse], summary="Список всех учителей", tags=["Teachers"])
async def get_teachers(
    q: Optional[str] = Query(None, description="Поиск по имени, никнейму или предмету"),
    db: Session = Depends(get_db)
):
    """
    Получить список всех учителей с возможностью поиска
    """
    query = db.query(User).filter(User.is_teacher == True)
    
    if q:
        # Поиск по текстовым полям
        text_condition = or_(
            User.nickname.ilike(f"%{q}%"),
            User.fullname.ilike(f"%{q}%"),
            User.email.ilike(f"%{q}%"),
            User.speciality.ilike(f"%{q}%")
        )
        query = query.filter(text_condition)
    
    teachers = query.all()
    return teachers

@app.get("/teachers/{teacher_id}", response_model=TeacherResponse, summary="Получить учителя по ID", tags=["Teachers"])
async def get_teacher(teacher_id: int, db: Session = Depends(get_db)):
    """
    Получить информацию об учителе по его ID
    """
    teacher = db.query(User).filter(User.id == teacher_id, User.is_teacher == True).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return teacher

@app.put("/teachers/{teacher_id}", response_model=TeacherResponse, summary="Обновить учителя", tags=["Teachers"])
async def update_teacher(
    teacher_id: int, 
    teacher_update: TeacherUpdate, 
    db: Session = Depends(get_db)
):
    """
    Обновить информацию об учителе
    """
    teacher = db.query(User).filter(User.id == teacher_id, User.is_teacher == True).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    if teacher_update.fullname is not None:
        teacher.fullname = teacher_update.fullname
    if teacher_update.email is not None:
        # Проверяем уникальность email
        existing = db.query(User).filter(User.email == teacher_update.email, User.id != teacher_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        teacher.email = teacher_update.email
    if teacher_update.speciality is not None:
        teacher.speciality = teacher_update.speciality
    if teacher_update.teacher_info is not None:
        teacher.teacher_info = teacher_update.teacher_info.dict()

    db.commit()
    db.refresh(teacher)
    return teacher

@app.delete("/teachers/{teacher_id}", summary="Удалить учителя", tags=["Teachers"])
async def delete_teacher(teacher_id: int, db: Session = Depends(get_db)):
    """
    Удалить учителя по ID
    """
    teacher = db.query(User).filter(User.id == teacher_id, User.is_teacher == True).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    # Удаляем аватар
    if teacher.avatar:
        filepath = os.path.join(AVATAR_DIR, teacher.avatar)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError as e:
                print(f"Ошибка при удалении файла {filepath}: {e}")
    
    # Удаляем из проектов
    all_projects = db.query(Project).all()
    for project in all_projects:
        if teacher_id in (project.authors_ids or []):
            authors = list(project.authors_ids)
            authors.remove(teacher_id)
            project.authors_ids = authors
    
    db.delete(teacher)
    db.commit()
    return {"message": f"Teacher {teacher_id} deleted successfully"}

# ==================== COMMON USER ENDPOINTS ====================

@app.get("/users/me", response_model=UserResponse, tags=["Common"])
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Получение информации о текущем пользователе по JWT токену
    """
    return current_user

@app.get("/users/{user_id}", response_model=UserResponse, tags=["Common"])
async def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    """
    Получить любого пользователя по ID (ученика или учителя)
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/users/", response_model=List[UserResponse], summary="Поиск всех пользователей", tags=["Common"])
async def search_all_users(
    q: Optional[str] = Query(None, description="Поисковый запрос"),
    user_type: Optional[str] = Query(None, description="Фильтр по типу: student или teacher"),
    db: Session = Depends(get_db)
):
    """
    Поиск по всем пользователям с возможностью фильтрации по типу
    """
    query = db.query(User)
    
    if user_type == "student":
        query = query.filter(User.is_teacher == False)
    elif user_type == "teacher":
        query = query.filter(User.is_teacher == True)
    
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

@app.post("/users/{user_id}/avatar", response_model=UserResponse, tags=["Common"])
async def upload_avatar(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Загрузить аватар для пользователя (только для своего профиля)
    """
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Can only update your own avatar")
    
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

# ==================== PROJECTS ====================

@app.post("/projects/", response_model=ProjectResponse, summary="Создать проект", tags=["Projects"])
async def create_project(
    project: ProjectCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Создать новый проект (автор должен быть текущим пользователем)
    """
    # Проверяем, что первый автор - текущий пользователь
    if project.authors_ids[0] != current_user.id:
        raise HTTPException(status_code=403, detail="First author must be the current user")
    
    # Проверяем существование всех авторов
    authors = db.query(User).filter(User.id.in_(project.authors_ids)).all()
    if len(authors) != len(project.authors_ids):
        raise HTTPException(status_code=404, detail="Один или несколько авторов не найдены")
    
    db_project = Project(
        title=project.title,
        body=project.body,
        underbody=project.underbody,
        authors_ids=project.authors_ids,
        tasks=project.tasks,
        links=project.links,
        comments=[]
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@app.get("/projects/", response_model=List[ProjectResponse], summary="Список проектов", tags=["Projects"])
async def get_projects(
    author_id: Optional[int] = Query(None, description="ID автора для фильтрации проектов"),
    db: Session = Depends(get_db)
):
    """
    Получить список всех проектов с возможностью фильтрации по автору
    """
    if author_id is not None:
        all_projects = db.query(Project).all()
        projects = [p for p in all_projects if author_id in (p.authors_ids or [])]
    else:
        projects = db.query(Project).all()
    return projects

@app.get("/projects/{project_id}", response_model=ProjectResponse, summary="Конкретный проект", tags=["Projects"])
async def get_project_by_id(project_id: int, db: Session = Depends(get_db)):
    """
    Получить проект по ID
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@app.put("/projects/{project_id}", response_model=ProjectResponse, summary="Обновление проекта", tags=["Projects"])
async def update_project(
    project_id: int, 
    project_update: ProjectUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Обновить проект (только для авторов)
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Проверяем, что текущий пользователь - автор проекта
    if current_user.id not in (project.authors_ids or []):
        raise HTTPException(status_code=403, detail="Only authors can update the project")

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
        project.comments = [comment.dict() for comment in project_update.comments]

    if project_update.authors_ids is not None:
        # Проверяем существование всех авторов
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

@app.post("/projects/{project_id}/comments", response_model=ProjectResponse, tags=["Projects"])
async def add_comment(
    project_id: int,
    comment: Comment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Добавить комментарий к проекту
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.comments is None:
        project.comments = []
    
    # Убеждаемся, что authorId совпадает с текущим пользователем
    comment.authorId = current_user.id
    
    project.comments.append(comment.dict())
    db.commit()
    db.refresh(project)
    return project

@app.get("/search", response_model=List[ProjectResponse], summary="Поиск проектов", tags=["Projects"])
async def search_projects(
    q: Optional[str] = Query(None, description="Строка для поиска по названию"),
    db: Session = Depends(get_db)
):
    """
    Поиск проектов по названию
    """
    if not q:
        return []
    projects = db.query(Project).filter(Project.title.ilike(f"%{q}%")).all()
    return projects

@app.delete("/projects/{project_id}", summary="Удалить проект", tags=["Projects"])
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Удалить проект (только для авторов)
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Проверяем, что текущий пользователь - автор проекта
    if current_user.id not in (project.authors_ids or []):
        raise HTTPException(status_code=403, detail="Only authors can delete the project")
    
    db.delete(project)
    db.commit()
    return {"message": f"Project {project_id} deleted successfully"}

# ==================== AUTH & VERIFICATION ====================

@app.post("/auth/request-verification-code", tags=["Auth"])
async def request_verification_code(
    request: dict,  # Оставляем как есть, но добавим отладку
    db: Session = Depends(get_db)
):
    """
    Запрашивает код подтверждения на указанный email
    """
    print(f"📨 Получен запрос на verification-code: {request}")
    
    email = request.get("email")
    is_teacher = request.get("is_teacher", False)
    
    print(f"📧 Email: {email}, is_teacher: {is_teacher}")
    
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    # Для учителей проверяем, разрешен ли email
    if is_teacher and not is_email_accepted(email):
        raise HTTPException(
            status_code=403,
            detail="Этот email не разрешен для регистрации учителя"
        )
    
    # Проверяем, не занят ли email
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Генерируем код и сохраняем на 10 минут
    code = generate_verification_code()
    redis_client.setex(f"verify:{email}", 600, code)
    
    # Отправляем код по email
    await send_verification_email(email, code)
    
    print(f"✅ Код отправлен на {email}")
    
    return {"message": "Verification code sent"}

@app.post("/auth/request-verification", tags=["Auth"])
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

@app.post("/auth/verify-email", tags=["Auth"])
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

@app.post("/auth/register-with-verification", response_model=UserResponse, tags=["Auth"])
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
    is_teacher = request.get("is_teacher", False)
    
    if not email or not code or not user_data:
        raise HTTPException(status_code=400, detail="Email, code and user data required")
    
    stored_code = redis_client.get(f"verify:{email}")
    if not stored_code or stored_code != code:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")
    
    redis_client.delete(f"verify:{email}")
    
    # Для учителей проверяем email
    if is_teacher and not is_email_accepted(email):
        raise HTTPException(
            status_code=403,
            detail="Этот email не разрешен для регистрации учителя"
        )
    
    existing_user = db.query(User).filter(
        (User.nickname == user_data.get('nickname')) | 
        (User.email == email)
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Nickname or email already registered")
    
    hashed_password = get_password_hash(user_data.get('password'))
    
    # Подготовка данных в зависимости от типа пользователя
    if is_teacher:
        # Регистрация учителя
        teacher_info = user_data.get('teacher_info', {})
        db_user = User(
            nickname=user_data.get('nickname').strip(),
            fullname=user_data.get('fullname'),
            class_=None,
            speciality=user_data.get('speciality'),
            email=email,
            password=hashed_password,
            avatar=None,
            is_verified=True,
            is_active=True,
            is_teacher=True,
            teacher_info=teacher_info
        )
    else:
        # Регистрация ученика
        db_user = User(
            nickname=user_data.get('nickname').strip(),
            fullname=user_data.get('fullname'),
            class_=user_data.get('class_', 0),
            speciality=user_data.get('speciality'),
            email=email,
            password=hashed_password,
            avatar=None,
            is_verified=True,
            is_active=True,
            is_teacher=False,
            teacher_info=None
        )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/auth/login", response_model=TokenResponse, tags=["Auth"])
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
    
    # Проверка пароля
    if not verify_password(credentials.password.strip(), user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")
    
    access_token = create_access_token({"sub": str(user.id), "is_teacher": user.is_teacher})
    refresh_token = create_refresh_token({"sub": str(user.id), "is_teacher": user.is_teacher})
    
    redis_client.setex(
        f"refresh:{user.id}:{refresh_token}",
        REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        "valid"
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

@app.post("/auth/refresh", response_model=TokenResponse, tags=["Auth"])
async def refresh_token(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Обновление access токена с помощью refresh токена
    """
    refresh_token = request.headers.get("Authorization", "").replace("Bearer ", "")
    
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token required")
    
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
        
        # Проверяем, что токен ещё действителен в Redis
        if not redis_client.get(f"refresh:{user_id}:{refresh_token}"):
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")
        
        # Создаём новые токены
        new_access_token = create_access_token({"sub": str(user.id), "is_teacher": user.is_teacher})
        new_refresh_token = create_refresh_token({"sub": str(user.id), "is_teacher": user.is_teacher})
        
        # Удаляем старый refresh токен
        redis_client.delete(f"refresh:{user_id}:{refresh_token}")
        
        # Сохраняем новый
        redis_client.setex(
            f"refresh:{user_id}:{new_refresh_token}",
            REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            "valid"
        )
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token
        )
        
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@app.post("/auth/logout", tags=["Auth"])
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Выход из системы (удаление refresh токена)
    """
    refresh_token = request.headers.get("Authorization", "").replace("Bearer ", "")
    
    if refresh_token:
        redis_client.delete(f"refresh:{current_user.id}:{refresh_token}")
    
    return {"message": "Logged out successfully"}

# ==================== ADMIN UTILITIES ====================

@app.delete("/admin/users/all", summary="Удалить всех пользователей (только для разработки)", tags=["Admin"])
async def delete_all_users(db: Session = Depends(get_db)):
    """
    Удалить всех пользователей (только для разработки!)
    """
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

@app.delete("/admin/projects/all", summary="Удалить все проекты (только для разработки)", tags=["Admin"])
async def delete_all_projects(db: Session = Depends(get_db)):
    """
    Удалить все проекты (только для разработки!)
    """
    count = db.query(Project).delete()
    db.commit()
    return {"message": f"Удалено проектов: {count}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)