from fastapi import FastAPI, Depends, HTTPException
import uvicorn
from pydantic import BaseModel, ConfigDict
from sqlalchemy import create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware






app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить запросы с любых сайтов
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить любые HTTP-методы (GET, POST и т.д.)
    allow_headers=["*"],  # Разрешить любые HTTP-заголовки
)

engine = create_engine('sqlite:///db.sqlite3')

class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True,autoincrement=True)
    name: Mapped[str] = mapped_column()
    email: Mapped[str] = mapped_column()
    password: Mapped[str] = mapped_column()

def create_session():
    session = sessionmaker(bind=engine)
    db = session()
    yield db

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)



class UserCreate(BaseModel):
    name: str
    email: str
    password: str

    model_config = ConfigDict(from_attributes=True)







@app.get('/')
def index():
    return {'status': 'ok'}


@app.get('/db/get_all_users')
def return_all_users(
        session: Session = Depends(create_session)
):
    with session as sess:
        tmp = select(User)
        data = sess.execute(tmp).scalars().all()


    return {'status':'ok','data':data}


@app.post('/db/create_user')
def create_user(user: UserCreate,session: Session = Depends(create_session)):
    debug_data = None
    with session as sess:
        new_user = User(
            name=user.name,
            email=user.email,
            password=user.password,
        )
        sess.add(new_user)
        sess.commit()
        stmt = select(User).where(User.name == new_user.name)
        debug_data = sess.scalars(stmt).one_or_none()

    return {'status':'ok','debug_data': debug_data}

@app.get("/db/users/{uid}")
def get_user_by_id(
    uid: int,  # Имя совпадает с {uid} в пути
    password: str,  # Пойдет в Query-параметры (?password=...)
    db: Session = Depends(create_session),  # Зависимость возвращает сессию
):
    # Работаем напрямую с db, без блока with
    stmt = select(User).where(User.id == uid, User.password == password)
    user = db.scalars(stmt).one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {'status':'ok','data': user}








if __name__ == '__main__':
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5757,
        reload=True)