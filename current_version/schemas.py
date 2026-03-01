from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, Dict, Any, List

# ---------- User ----------
class UserBase(BaseModel):
    nickname: str
    fullname: str
    class_: float = Field(
        0.0,
        validation_alias="class",        
        serialization_alias="class"     
    )
    speciality: Optional[str] = None
    email: EmailStr

class UserResponse(UserBase):
    id: int
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True           
    )

class UserCreate(UserBase):
    password: str 

class LoginRequest(BaseModel):
    nickname: str
    password: str

    
class UserUpdate(BaseModel):
    fullname: Optional[str] = None
    email: Optional[EmailStr] = None
    class_: Optional[float] = Field(None, alias="class") 
    speciality: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)
# ---------- Teacher ----------
class TeacherBase(UserBase):
    prof: str  

class TeacherCreate(TeacherBase):
    password: str

class TeacherResponse(TeacherBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# ---------- Project ----------
class ProjectBase(BaseModel):
    title: str = Field(..., min_length=1, json_schema_extra={"example": "Космическая программа"})
    body: str = Field(..., min_length=1, json_schema_extra={"example": "Подробное описание..."})
    underbody: str = Field("", json_schema_extra={"example": "Дополнительные материалы"})
    tasks: List[Dict[str, Any]] = Field(
        default=[],
        json_schema_extra={
            "example": [
                {"title": "расчёты", "status": "в процессе", "body": "очень важная задача", "timelinend": "20.11.2026", "timeline":"15.10.2025"},
                {"title": "разработка интерфейса", "status": "в работе", "body": "создать адаптивный дизайн", "timelinend": "01.12.2026", "timeline":"15.10.2025"},
                {"title": "тестирование", "status": "ожидает", "body": "проверить всё", "timelinend": "10.12.2026", "timeline":"15.10.2025"}
            ]
        }
    )

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