from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

# ---------- Comment Schema ----------
class Comment(BaseModel):
    id: str
    authorId: int
    content: str
    createdAt: str
    isRead: bool

# ---------- User Base (общая база) ----------
class UserBase(BaseModel):
    nickname: str
    fullname: str
    email: EmailStr
    avatar: Optional[str] = None
    speciality: Optional[str] = None
    is_teacher: bool = False  # По умолчанию ученик

# ---------- Student (ученик) ----------
class StudentBase(UserBase):
    class_: float = Field(
        0.0,
        alias="class",
        validation_alias="class",
        serialization_alias="class"
    )
    is_teacher: bool = False  # Переопределяем, чтобы всегда было False

class StudentCreate(StudentBase):
    password: str
    
    @field_validator('is_teacher')
    def validate_is_teacher(cls, v):
        if v is True:
            raise ValueError('Student cannot be a teacher')
        return v

class StudentResponse(StudentBase):
    id: int
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class StudentUpdate(BaseModel):
    fullname: Optional[str] = None
    email: Optional[EmailStr] = None
    class_: Optional[float] = Field(None, alias="class")
    speciality: Optional[str] = None
    avatar: Optional[str] = None
    model_config = ConfigDict(populate_by_name=True)

# ---------- Teacher (учитель) ----------
class TeacherRole(str, Enum):
    CUSTOMER = "customer"      # Заказчик
    EXPERT = "expert"           # Эксперт
    SUPERVISOR = "supervisor"   # Научный руководитель
    # Куратор не включён в список, так как выбирается отдельным чекбоксом

class TeacherInfo(BaseModel):
    roles: List[TeacherRole] = Field(default=[], description="Роли учителя: заказчик, эксперт, научный руководитель")
    curator: bool = Field(default=False, description="Является ли куратором (отдельная роль)")

class TeacherBase(UserBase):
    is_teacher: bool = True
    teacher_info: TeacherInfo


class TeacherCreate(TeacherBase):
    password: str

class TeacherResponse(TeacherBase):
    id: int
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class TeacherUpdate(BaseModel):
    fullname: Optional[str] = None
    email: Optional[EmailStr] = None
    speciality: Optional[str] = None
    avatar: Optional[str] = None
    teacher_info: Optional[TeacherInfo] = None
    model_config = ConfigDict(populate_by_name=True)

# ---------- Общий пользователь (для списков и базовых операций) ----------
class UserResponse(BaseModel):
    id: int
    nickname: str
    fullname: str
    email: EmailStr
    avatar: Optional[str] = None
    speciality: Optional[str] = None
    is_active: bool
    is_verified: bool
    is_teacher: bool
    # Поля, которые могут быть только у учеников
    class_: Optional[float] = Field(None, alias="class")
    # Поля, которые могут быть только у учителей
    teacher_info: Optional[TeacherInfo] = None
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

# ---------- Auth ----------
class LoginRequest(BaseModel):
    nickname: str
    password: str

# ---------- Project ----------
class ProjectBase(BaseModel):
    title: str = Field(..., min_length=1, json_schema_extra={"example": "Космическая программа"})
    body: str = Field(..., min_length=1, json_schema_extra={"example": "Подробное описание..."})
    underbody: str = Field("", json_schema_extra={"example": "Дополнительные материалы"})
    tasks: List[Dict[str, Any]] = Field(
        default=[],
        json_schema_extra={
            "example": [
                {"title": "расчёты", "status": "в процессе", "body": "очень важная задача", "timelinend": "20.11.2026", "timeline": "15.10.2025"},
                {"title": "разработка интерфейса", "status": "в работе", "body": "создать адаптивный дизайн", "timelinend": "01.12.2026", "timeline": "15.10.2025"},
                {"title": "тестирование", "status": "ожидает", "body": "проверить всё", "timelinend": "10.12.2026", "timeline": "15.10.2025"}
            ]
        }
    )
    links: Optional[Dict[str, str]] = Field(
        default=None,
        json_schema_extra={"example": {"github": "https://github.com/...", "google_drive": "https://drive.google.com/..."}}
    )
    comments: List[Comment] = Field(default=[], description="Комментарии к проекту")

class ProjectCreate(ProjectBase):
    authors_ids: List[int] = Field(..., description="Список ID всех авторов")

class ProjectResponse(ProjectBase):
    id: int
    authors_ids: List[int] = Field(..., description="Список ID всех авторов проекта")
    model_config = ConfigDict(from_attributes=True)

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    underbody: Optional[str] = None
    tasks: Optional[List[Dict[str, Any]]] = None
    authors_ids: Optional[List[int]] = Field(None, description="Полный список ID авторов") 
    author_id: Optional[int] = Field(None, description="ID автора для добавления к существующему списку")
    links: Optional[Dict[str, str]] = Field(
        default=None,
        json_schema_extra={"example": {"github": "https://github.com/...", "google_drive": "https://drive.google.com/..."}}
    )
    comments: Optional[List[Comment]] = Field(default=None, description="Комментарии к проекту")

# ---------- Email верификация ----------
class EmailVerificationCodeRequest(BaseModel):
    email: EmailStr

class EmailVerificationRequest(BaseModel):
    email: EmailStr
    code: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

# ---------- Token схемы ----------
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"