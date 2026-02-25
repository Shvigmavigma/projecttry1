from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List

class UserBase(BaseModel):
    nickname: str
    fullname: str
    class_: float = Field(0.0, alias="class")  
    speciality: Optional[str] = None
    email: EmailStr
    project_id: Optional[int] = None

class UserCreate(UserBase):
    password: str 

class UserResponse(UserBase):
    id: int

    class Config:
        orm_mode = True  

class TeacherBase(UserBase):
    prof: str  

class TeacherCreate(TeacherBase):
    password: str

class TeacherResponse(TeacherBase):
    id: int

    class Config:
        orm_mode = True
    
class ProjectBase(BaseModel):
    title: str = Field(..., min_length=1, example="Космическая программа")
    body: str = Field(..., min_length=1, example="Подробное описание...")
    underbody: str = Field("", example="Дополнительные материалы")
    author_id: int = Field(..., example=1)
    tasks: List[Dict[str, Any]] = Field(
        default=[],
        example=[
    {"title": "расчёты", "status": "в процессе", "body": "очень важная задача", "timeline": "20.11.2026"},
    {"title": "разработка интерфейса", "status": "в работе", "body": "создать адаптивный дизайн", "timeline": "01.12.2026"},
    {"title": "тестирование", "status": "ожидает", "body": "проверить всё", "timeline": "10.12.2026"}
]
    )

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: int
    author: UserResponse
    class Config:
        orm_mode = True

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    underbody: Optional[str] = None
    tasks: Optional[List[Dict[str, Any]]] = None