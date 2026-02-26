from fastapi import FastAPI, HTTPException, Query, Depends
import uvicorn
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_, text
from fastapi.middleware.cors import CORSMiddleware

from models import Base, User, Project
from database import engine, session_local
from schemas import (
    UserResponse, UserCreate,
    ProjectResponse, ProjectCreate, ProjectUpdate,
    TeacherCreate, TeacherResponse
)

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

# ---------- USERS ----------
@app.post("/users/", response_model=UserResponse, summary="Создать юзера", tags=["USERDB"])
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Не забудьте хешировать пароль перед сохранением!
    db_user = User(
        nickname=user.nickname,
        fullname=user.fullname,
        class_=user.class_,
        speciality=user.speciality,
        email=user.email,
        password=user.password  # TODO: заменить на hash_password(user.password)
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
    Удаляет всех пользователей из базы данных.
    Перед удалением во всех проектах поле authors_ids принудительно устанавливается в пустой массив '[]',
    чтобы полностью убрать ссылки на удаляемых пользователей.
    """
    db.execute(text("UPDATE projects SET authors_ids = '[]'"))

    deleted_count = db.query(User).delete()
    
    db.commit()
    return {
        "message": f"Удалено пользователей: {deleted_count}",
        "projects_updated": "всем проектам установлен пустой список авторов"
    }



@app.delete("/users/{user_id}", summary="Удалить пользователя по ID", tags=["USERDB"])
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Найти все проекты, где user_id есть в списке авторов
    all_projects = db.query(Project).all()
    projects_with_user = [p for p in all_projects if user_id in (p.authors_ids or [])]

    for project in projects_with_user:
        if user_id in project.authors_ids:

            x=list(project.authors_ids)
            x.remove(user_id)
            project.authors_ids=x


    # Удалить пользователя
    db.delete(user)
    db.commit()
    return {"message": f"User {user_id} deleted successfully and removed from projects authors"}


# ---------- PROJECTS ----------
@app.post("/projects/", response_model=ProjectResponse, summary="Создать проект", tags=["PROJECTDB"])
async def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    # Проверяем, что автор существует
    author = db.query(User).filter(User.id == project.authors_ids[0]).first()
    if not author:
        raise HTTPException(status_code=404, detail=f"Автор с ID {project.authors_ids[0]} не найден")
    db_project = Project(
        title=project.title,
        body=project.body,
        underbody=project.underbody,
        authors_ids=[project.authors_ids[0]],   # список с одним ID
        tasks=project.tasks
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@app.get("/projects/", response_model=List[ProjectResponse], summary="Список проектов", tags=["PROJECTDB"])
async def get_projects(db: Session = Depends(get_db)):
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

    # Обновляем основные поля
    if project_update.title is not None:
        project.title = project_update.title
    if project_update.body is not None:
        project.body = project_update.body
    if project_update.underbody is not None:
        project.underbody = project_update.underbody
    if project_update.tasks is not None:
        project.tasks = project_update.tasks


    if project_update.author_id is not None:
        # Проверка существования пользователя
        author = db.query(User).filter(User.id == project_update.author_id).first()
        if not author:
            raise HTTPException(status_code=404, detail=f"Автор с ID {project_update.author_id} не найден")

        # Убедится, что authors_ids — список 
        if project.authors_ids is None:
            project.authors_ids = []

        if project_update.author_id not in project.authors_ids:
            x=list(project.authors_ids)
            x.append(project_update.author_id)
            project.authors_ids=x
            print(f"Добавлен автор {project_update.author_id}, теперь список: {project.authors_ids}")
        else:
            print(f"Автор {project_update.author_id} уже есть в списке")

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

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)