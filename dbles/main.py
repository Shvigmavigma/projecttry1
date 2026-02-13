from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import Annotated
from sqlalchemy import select

app = FastAPI()

engine = create_async_engine('sqlite+aiosqlite:///books.db')
new_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_session():
    async with new_session() as session:
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_session)]

class Base(DeclarativeBase):
    pass

class BookModel(Base):
    __tablename__ = "books"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    author: Mapped[str]
    
@app.post("/setup_database")   
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    return {"ok": True, "msg": "all nice"}

class BookAddSchema(BaseModel):
    title: str
    author: str

class BookSchema(BookAddSchema):    
    id: int

@app.post("/books")
async def add_book(data: BookAddSchema, session: SessionDep): 
    new_book = BookModel(
        title=data.title,
        author=data.author
    )
    session.add(new_book)
    await session.commit()  
    return {"ok": True} 
    
@app.get("/books")
async def get_books(session: SessionDep): 
    query = select(BookModel)
    result = await session.execute(query)  
    books = result.scalars().all()  
    return books

@app.get("/books/{book_id}")
async def get_book(book_id: int, session: SessionDep):
    book = await session.get(BookModel, book_id)
    if not book:
        return {"error": "Book not found"}
    return book