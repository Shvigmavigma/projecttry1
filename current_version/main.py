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
from sqlalchemy.orm.attributes import flag_modified
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
    ProjectRole, Participant, ProjectCreate, ProjectResponse, ProjectUpdate, Comment,
    # Email schemas
    EmailVerificationCodeRequest, EmailVerificationRequest,
    PasswordResetRequest, PasswordResetConfirm,
    # Token schemas
    TokenResponse,
    # New schemas for suggestions and invitations
    Suggestion, SuggestionCreate, SuggestionStatus,
    InvitationCreate, InvitationInfo
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

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ПРОЕКТОВ ====================
def is_project_participant(project: Project, user_id: int) -> bool:
    """Проверяет, является ли пользователь участником проекта"""
    return any(p.get("user_id") == user_id for p in (project.participants or []))

def get_participant_role(project: Project, user_id: int) -> Optional[str]:
    """Возвращает роль пользователя в проекте или None"""
    for p in (project.participants or []):
        if p.get("user_id") == user_id:
            return p.get("role")
    return None

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

    # Удаляем пользователя из участников проектов
    all_projects = db.query(Project).all()
    for project in all_projects:
        if project.participants:
            new_participants = [p for p in project.participants if p.get("user_id") != student_id]
            if len(new_participants) != len(project.participants):
                project.participants = new_participants

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
    teacher_info_dict = teacher.teacher_info.model_dump() if teacher.teacher_info else {}

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
        teacher.teacher_info = teacher_update.teacher_info.model_dump()

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

    # Удаляем пользователя из участников проектов
    all_projects = db.query(Project).all()
    for project in all_projects:
        if project.participants:
            new_participants = [p for p in project.participants if p.get("user_id") != teacher_id]
            if len(new_participants) != len(project.participants):
                project.participants = new_participants

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

@app.post("/projects/{project_id}/join-requests", response_model=ProjectResponse, tags=["Projects"])
async def create_join_request(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Создать запрос на вступление в проект как исполнитель.
    Доступно только для учеников (не учителей), не являющихся участниками проекта.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Проверяем, что пользователь не участник
    if any(p.get("user_id") == current_user.id for p in (project.participants or [])):
        raise HTTPException(status_code=400, detail="You are already a participant")

    # Только ученики
    if current_user.is_teacher:
        raise HTTPException(status_code=403, detail="Only students can request to join as executor")

    # Проверяем, нет ли уже ожидающего запроса от этого пользователя
    if project.join_requests:
        existing = next((r for r in project.join_requests if r.get("user_id") == current_user.id and r.get("status") == "pending"), None)
        if existing:
            raise HTTPException(status_code=400, detail="You already have a pending request")

    # Создаём запрос
    new_request = {
        "id": str(uuid.uuid4()),
        "user_id": current_user.id,
        "created_at": datetime.utcnow().isoformat(),
        "status": "pending"
    }
    if project.join_requests is None:
        project.join_requests = []
    project.join_requests.append(new_request)

    # Помечаем поле как изменённое для SQLAlchemy
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(project, "join_requests")

    db.commit()
    db.refresh(project)
    return project

@app.put("/projects/{project_id}/join-requests/{request_id}/accept", response_model=ProjectResponse, tags=["Projects"])
async def accept_join_request(
    project_id: int,
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Принять запрос на вступление. Доступно только заказчику или куратору.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Проверяем роль текущего пользователя
    role = get_participant_role(project, current_user.id)
    if role not in [ProjectRole.CUSTOMER.value, ProjectRole.CURATOR.value]:
        raise HTTPException(status_code=403, detail="Only customer or curator can accept join requests")

    # Ищем запрос
    request = None
    for r in (project.join_requests or []):
        if r.get("id") == request_id:
            request = r
            break
    if not request:
        raise HTTPException(status_code=404, detail="Join request not found")
    if request.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")

    # Меняем статус
    request["status"] = "accepted"

    # Добавляем пользователя в участники с ролью executor
    new_participant = {
        "user_id": request["user_id"],
        "role": ProjectRole.EXECUTOR.value,
        "joined_at": datetime.utcnow().isoformat()
    }
    if project.participants is None:
        project.participants = []
    project.participants.append(new_participant)

    flag_modified(project, "join_requests")
    flag_modified(project, "participants")
    db.commit()
    db.refresh(project)
    return project

@app.put("/projects/{project_id}/join-requests/{request_id}/reject", response_model=ProjectResponse, tags=["Projects"])
async def reject_join_request(
    project_id: int,
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Отклонить запрос на вступление. Доступно только заказчику или куратору.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    role = get_participant_role(project, current_user.id)
    if role not in [ProjectRole.CUSTOMER.value, ProjectRole.CURATOR.value]:
        raise HTTPException(status_code=403, detail="Only customer or curator can reject join requests")

    request = None
    for r in (project.join_requests or []):
        if r.get("id") == request_id:
            request = r
            break
    if not request:
        raise HTTPException(status_code=404, detail="Join request not found")
    if request.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")

    request["status"] = "rejected"
    flag_modified(project, "join_requests")
    db.commit()
    db.refresh(project)
    return project


@app.post("/projects/", response_model=ProjectResponse, summary="Создать проект", tags=["Projects"])
async def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Создать новый проект. Текущий пользователь автоматически добавляется в участники,
    если его нет в списке participants. Роль определяется на основе его типа.
    """
    # Проверяем, есть ли текущий пользователь в списке участников
    creator_in_participants = any(p.user_id == current_user.id for p in project.participants)

    if not creator_in_participants:
        # Определяем роль по умолчанию на основе типа пользователя
        default_role = ProjectRole.EXECUTOR
        if current_user.is_teacher and current_user.teacher_info:
            roles = current_user.teacher_info.get("roles", [])
            if ProjectRole.CUSTOMER.value in roles:
                default_role = ProjectRole.CUSTOMER
            elif ProjectRole.SUPERVISOR.value in roles:
                default_role = ProjectRole.SUPERVISOR
            elif ProjectRole.EXPERT.value in roles:
                default_role = ProjectRole.EXPERT
            if current_user.teacher_info.get("curator"):
                default_role = ProjectRole.CURATOR

        # Добавляем текущего пользователя в participants
        project.participants.append(
            Participant(
                user_id=current_user.id,
                role=default_role,
                joined_at=datetime.utcnow()
            )
        )

    # Проверяем существование всех указанных пользователей
    user_ids = [p.user_id for p in project.participants]
    users = db.query(User).filter(User.id.in_(user_ids)).all()
    if len(users) != len(user_ids):
        raise HTTPException(status_code=404, detail="Один или несколько участников не найдены")

    # Создаём проект – используем mode='json' для сериализации
    db_project = Project(
        title=project.title,
        body=project.body,
        underbody=project.underbody,
        participants=[p.model_dump(mode='json') for p in project.participants],
        tasks=project.tasks,
        links=project.links,
        comments=[c.model_dump(mode='json') for c in project.comments] if project.comments else []
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@app.get("/projects/", response_model=List[ProjectResponse], summary="Список проектов", tags=["Projects"])
async def get_projects(
    participant_id: Optional[int] = Query(None, description="ID участника для фильтрации проектов"),
    db: Session = Depends(get_db)
):
    """
    Получить список всех проектов. Если указан participant_id, возвращаются только проекты,
    в которых пользователь является участником.
    """
    if participant_id is not None:
        all_projects = db.query(Project).all()
        projects = [
            p for p in all_projects
            if any(part.get("user_id") == participant_id for part in (p.participants or []))
        ]
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
    Обновить проект. Только заказчик или исполнитель могут вносить изменения.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Проверяем, что текущий пользователь является заказчиком или исполнителем
    participant = next(
        (p for p in project.participants if p.get("user_id") == current_user.id),
        None
    )
    if not participant or participant.get("role") not in [ProjectRole.CUSTOMER.value, ProjectRole.EXECUTOR.value]:
        raise HTTPException(status_code=403, detail="Only customer or executor can update the project")

    # Обновляем поля, если они переданы
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
        # Используем mode='json' для сериализации
        project.comments = [c.model_dump(mode='json') for c in project_update.comments]
    if project_update.participants is not None:
        # Проверяем существование новых участников
        new_ids = [p.user_id for p in project_update.participants]
        users = db.query(User).filter(User.id.in_(new_ids)).all()
        if len(users) != len(new_ids):
            raise HTTPException(404, "One or more users not found")
        project.participants = [p.model_dump(mode='json') for p in project_update.participants]

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
    Добавить комментарий к проекту. Может любой участник проекта.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Проверяем, что пользователь является участником проекта
    if not any(p.get("user_id") == current_user.id for p in (project.participants or [])):
        raise HTTPException(status_code=403, detail="Only project participants can comment")

    if project.comments is None:
        project.comments = []

    comment.authorId = current_user.id
    # Создаём новый список, чтобы SQLAlchemy отследил изменение
    new_comments = project.comments + [comment.model_dump(mode='json')]
    project.comments = new_comments

    try:
        db.commit()
        db.refresh(project)
        return project
    except Exception as e:
        print("Ошибка при сохранении комментария:", e)
        raise HTTPException(status_code=500, detail="Internal server error")

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
    Удалить проект. Только заказчик (роль customer) может удалить проект.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Проверяем, что текущий пользователь является заказчиком
    participant = next(
        (p for p in project.participants if p.get("user_id") == current_user.id),
        None
    )
    if not participant or participant.get("role") != ProjectRole.CUSTOMER.value:
        raise HTTPException(status_code=403, detail="Only customer can delete the project")

    db.delete(project)
    db.commit()
    return {"message": f"Project {project_id} deleted successfully"}

@app.post("/projects/{project_id}/tasks/{task_index}/comments", response_model=ProjectResponse, tags=["Projects"])
async def add_task_comment(
    project_id: int,
    task_index: int,
    comment: Comment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Добавить комментарий к задаче. Может любой участник проекта.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Проверяем, что пользователь является участником проекта
    if not any(p.get("user_id") == current_user.id for p in (project.participants or [])):
        raise HTTPException(status_code=403, detail="Only project participants can comment")

    if not project.tasks or task_index < 0 or task_index >= len(project.tasks):
        raise HTTPException(status_code=404, detail="Task not found")

    task = project.tasks[task_index]
    if task.get("comments") is None:
        task["comments"] = []

    comment.authorId = current_user.id

    new_task_comments = task["comments"] + [comment.model_dump(mode='json')]
    task["comments"] = new_task_comments

    flag_modified(project, "tasks")

    try:
        db.commit()
        db.refresh(project)
        return project
    except Exception as e:
        print("Ошибка при сохранении комментария к задаче:", e)
        raise HTTPException(status_code=500, detail="Internal server error")

# ==================== НОВЫЕ ЭНДПОИНТЫ ДЛЯ ПРЕДЛОЖЕНИЙ ====================

@app.post("/projects/{project_id}/suggestions", response_model=ProjectResponse, tags=["Projects"])
async def create_suggestion(
    project_id: int,
    suggestion_data: SuggestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Создать предложение по изменению проекта (только для экспертов и научруков, и исполнителей).
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Проверяем, что пользователь участник и имеет роль эксперт, научрук или исполнитель
    role = get_participant_role(project, current_user.id)
    if not role or role not in [ProjectRole.EXPERT.value, ProjectRole.SUPERVISOR.value, ProjectRole.EXECUTOR.value]:
        raise HTTPException(status_code=403, detail="Only expert, supervisor or executor can create suggestions")

    # Валидация target_type
    if suggestion_data.target_type not in ["project", "task", "link"]:
        raise HTTPException(status_code=400, detail="target_type must be 'project', 'task', or 'link'")

    # Создаём предложение
    new_suggestion = {
        "id": str(uuid.uuid4()),
        "author_id": current_user.id,
        "target_type": suggestion_data.target_type,
        "target_id": suggestion_data.target_id,
        "changes": suggestion_data.changes,
        "status": SuggestionStatus.PENDING.value,
        "created_at": datetime.utcnow().isoformat(),
        "comments": []
    }

    if project.suggestions is None:
        project.suggestions = []
    project.suggestions.append(new_suggestion)
    flag_modified(project, "suggestions")
    db.commit()
    db.refresh(project)
    return project

@app.put("/projects/{project_id}/suggestions/{suggestion_id}/accept", response_model=ProjectResponse, tags=["Projects"])
async def accept_suggestion(
    project_id: int,
    suggestion_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Принять предложение. Может принять автор предложения или заказчик, а также исполнитель.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    suggestion = None
    for s in (project.suggestions or []):
        if s.get("id") == suggestion_id:
            suggestion = s
            break
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    role = get_participant_role(project, current_user.id)
    if not (suggestion.get("author_id") == current_user.id or role in [ProjectRole.CUSTOMER.value, ProjectRole.EXECUTOR.value]):
        raise HTTPException(status_code=403, detail="Only suggestion author, customer or executor can accept it")

    suggestion["status"] = SuggestionStatus.ACCEPTED.value
    flag_modified(project, "suggestions")  # <-- обязательно

    # Если принял заказчик и предложение касается проекта, автоматически применяем изменения
    if role == ProjectRole.CUSTOMER.value and suggestion["target_type"] == "project":
        for key, value in suggestion["changes"].items():
            if hasattr(project, key):
                setattr(project, key, value)

    db.commit()
    db.refresh(project)
    return project

@app.put("/projects/{project_id}/suggestions/{suggestion_id}/reject", response_model=ProjectResponse, tags=["Projects"])
async def reject_suggestion(
    project_id: int,
    suggestion_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Отклонить предложение. Может отклонить автор или заказчик, а также исполнитель.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    suggestion = None
    for s in (project.suggestions or []):
        if s.get("id") == suggestion_id:
            suggestion = s
            break
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    role = get_participant_role(project, current_user.id)
    if not (suggestion.get("author_id") == current_user.id or role in [ProjectRole.CUSTOMER.value, ProjectRole.EXECUTOR.value]):
        raise HTTPException(status_code=403, detail="Only suggestion author, customer or executor can reject it")

    suggestion["status"] = SuggestionStatus.REJECTED.value
    flag_modified(project, "suggestions")  # <-- обязательно
    db.commit()
    db.refresh(project)
    return project

# ==================== СКРЫТИЕ КОММЕНТАРИЕВ ====================

@app.post("/projects/{project_id}/comments/{comment_id}/hide", response_model=ProjectResponse, tags=["Projects"])
async def hide_comment(
    project_id: int,
    comment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Скрыть комментарий (только для научного руководителя).
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Проверяем, что пользователь научный руководитель
    role = get_participant_role(project, current_user.id)
    if role != ProjectRole.SUPERVISOR.value:
        raise HTTPException(status_code=403, detail="Only supervisor can hide comments")

    # Ищем комментарий
    comment = None
    for c in (project.comments or []):
        if c.get("id") == comment_id:
            comment = c
            break
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    comment["hidden"] = True
    flag_modified(project, "comments")
    db.commit()
    db.refresh(project)
    return project

# ==================== ПРИГЛАШЕНИЯ ====================

@app.post("/projects/{project_id}/invite", response_model=Dict[str, str], tags=["Projects"])
async def create_invitation(
    project_id: int,
    invite: InvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Создать приглашение в проект (только заказчик или научрук).
    Возвращает токен для приглашения.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Проверяем права: заказчик или научрук
    role = get_participant_role(project, current_user.id)
    if role not in [ProjectRole.CUSTOMER.value, ProjectRole.SUPERVISOR.value]:
        raise HTTPException(status_code=403, detail="Only customer or supervisor can invite")

    # Генерируем уникальный токен
    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(days=7)

    # Сохраняем в Redis: invite:{token} -> данные
    invite_data = {
        "project_id": project_id,
        "project_title": project.title,
        "role": invite.role.value,
        "invited_by": current_user.id,
        "email": invite.email,
        "expires_at": expires_at.isoformat()
    }
    redis_client.setex(f"invite:{token}", 7 * 24 * 60 * 60, json.dumps(invite_data))

    # Здесь можно отправить email со ссылкой http://frontend/invite/{token}
    # await send_invitation_email(invite.email, token, project.title)

    return {"token": token, "message": "Invitation created, email sending not implemented"}

@app.get("/invite/{token}", response_model=InvitationInfo, tags=["Invitations"])
async def get_invitation_info(token: str):
    """
    Получить информацию о приглашении по токену.
    """
    data_str = redis_client.get(f"invite:{token}")
    if not data_str:
        raise HTTPException(status_code=404, detail="Invitation not found or expired")
    data = json.loads(data_str)
    return InvitationInfo(
        token=token,
        project_id=data["project_id"],
        project_title=data["project_title"],
        role=data["role"],
        invited_by=data["invited_by"],
        expires_at=datetime.fromisoformat(data["expires_at"])
    )

@app.post("/invite/{token}/accept", response_model=ProjectResponse, tags=["Invitations"])
async def accept_invitation(
    token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Принять приглашение. Текущий пользователь добавляется в участники проекта с указанной ролью.
    """
    data_str = redis_client.get(f"invite:{token}")
    if not data_str:
        raise HTTPException(status_code=404, detail="Invitation not found or expired")
    data = json.loads(data_str)

    project = db.query(Project).filter(Project.id == data["project_id"]).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Проверяем, не является ли уже пользователь участником
    if any(p.get("user_id") == current_user.id for p in (project.participants or [])):
        raise HTTPException(status_code=400, detail="User already in project")

    # Добавляем участника
    new_participant = {
        "user_id": current_user.id,
        "role": data["role"],
        "joined_at": datetime.utcnow().isoformat(),
        "invited_by": data["invited_by"]
    }
    if project.participants is None:
        project.participants = []
    project.participants.append(new_participant)

    # Удаляем использованный токен
    redis_client.delete(f"invite:{token}")

    db.commit()
    db.refresh(project)
    return project

# ==================== AUTH & VERIFICATION ====================

@app.post("/auth/request-verification-code", tags=["Auth"])
async def request_verification_code(
    request: dict,
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
        raise HTTPException(
            status_code=402,
            detail="Пользователь с таким логином не найден"
        )

    # Проверка пароля
    if not verify_password(credentials.password.strip(), user.password):
        raise HTTPException(
            status_code=402,
            detail="Неверный пароль"
        )

    # Проверка активности
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Аккаунт деактивирован"
        )

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

    # Очищаем участников проектов (проекты остаются без участников)
    projects = db.query(Project).all()
    for p in projects:
        p.participants = []

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

# ==================== УДАЛЕНИЕ КОММЕНТАРИЕВ ПРОЕКТА ====================

@app.delete("/projects/{project_id}/comments/{comment_id}", response_model=ProjectResponse, tags=["Projects"])
async def delete_project_comment(
    project_id: int,
    comment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Удалить (скрыть) комментарий проекта. Может автор комментария или заказчик.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not any(p.get("user_id") == current_user.id for p in (project.participants or [])):
        raise HTTPException(status_code=403, detail="Only project participants can modify comments")

    # Ищем комментарий
    comment = None
    for c in (project.comments or []):
        if c.get("id") == comment_id:
            comment = c
            break
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Проверяем права: автор комментария или заказчик
    role = get_participant_role(project, current_user.id)
    if not (comment.get("authorId") == current_user.id or role == ProjectRole.CUSTOMER.value):
        raise HTTPException(status_code=403, detail="Only comment author or customer can delete")

    # Помечаем как скрытый
    comment["hidden"] = True
    flag_modified(project, "comments")
    db.commit()
    db.refresh(project)
    return project

# ==================== УДАЛЕНИЕ КОММЕНТАРИЕВ ЗАДАЧИ ====================

@app.delete("/projects/{project_id}/tasks/{task_index}/comments/{comment_id}", response_model=ProjectResponse, tags=["Projects"])
async def delete_task_comment(
    project_id: int,
    task_index: int,
    comment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    print(f"=== DELETE TASK COMMENT ===")
    print(f"User {current_user.id} (role: {get_participant_role(project, current_user.id)})")
    print(f"Project participants: {project.participants}")

    if not any(p.get("user_id") == current_user.id for p in (project.participants or [])):
        raise HTTPException(status_code=403, detail="Only project participants can modify comments")

    if not project.tasks or task_index < 0 or task_index >= len(project.tasks):
        raise HTTPException(status_code=404, detail="Task not found")

    task = project.tasks[task_index]
    print(f"Task before: {task}")

    if task.get("comments") is None:
        raise HTTPException(status_code=404, detail="Comments not found")

    comment = None
    for c in task["comments"]:
        if c.get("id") == comment_id:
            comment = c
            break
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    print(f"Comment found: {comment}")
    print(f"Comment authorId: {comment.get('authorId')}, current user: {current_user.id}")

    role = get_participant_role(project, current_user.id)
    if not (comment.get("authorId") == current_user.id or role == ProjectRole.CUSTOMER.value):
        raise HTTPException(status_code=403, detail="Only comment author or customer can delete")

    comment["hidden"] = True
    print(f"Comment after marking hidden: {comment}")

    flag_modified(project, "tasks")

    db.commit()
    db.refresh(project)
    print(f"Task after commit: {project.tasks[task_index]}")
    return project

# ==================== ОБНОВЛЕНИЕ КОММЕНТАРИЕВ ЗАДАЧИ ====================
@app.put("/projects/{project_id}/comments/{comment_id}/read", response_model=ProjectResponse, tags=["Projects"])
async def mark_project_comment_read(
    project_id: int,
    comment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not any(p.get("user_id") == current_user.id for p in (project.participants or [])):
        raise HTTPException(status_code=403, detail="Only project participants can modify comments")

    comment = next((c for c in (project.comments or []) if c.get("id") == comment_id), None)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    comment["isRead"] = True
    flag_modified(project, "comments")
    db.commit()
    db.refresh(project)
    return project

@app.put("/projects/{project_id}/tasks/{task_index}/comments/{comment_id}/read", response_model=ProjectResponse, tags=["Projects"])
async def mark_task_comment_read(
    project_id: int,
    task_index: int,
    comment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not any(p.get("user_id") == current_user.id for p in (project.participants or [])):
        raise HTTPException(status_code=403, detail="Only project participants can modify comments")

    if not project.tasks or task_index < 0 or task_index >= len(project.tasks):
        raise HTTPException(status_code=404, detail="Task not found")

    task = project.tasks[task_index]
    comment = next((c for c in (task.get("comments") or []) if c.get("id") == comment_id), None)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    comment["isRead"] = True
    flag_modified(project, "tasks")
    db.commit()
    db.refresh(project)
    return project

# Кастомный обработчик OPTIONS (удалён, чтобы избежать конфликта с CORSMiddleware)
# Если нужны дополнительные заголовки, лучше настроить CORSMiddleware.
# Оставляем только CORSMiddleware, который уже настроен выше.

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)