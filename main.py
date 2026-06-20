from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta


from database import Base, engine, get_db
from category import router as category_router
from product import router as product_router
from order import router as order_router


from sqlalchemy import Column, Integer, String
from fastapi.security import OAuth2PasswordBearer


import bcrypt
from jose import jwt


# =========================
# 1. FASTAPI APP
# =========================
app = FastAPI()


# 👇 MUST be after app creation
app.include_router(category_router)
app.include_router(product_router)
app.include_router(order_router)


# =========================
# 2. USER MODEL
# =========================
class User(Base):
    __tablename__ = "users"


    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)


# Create tables
Base.metadata.create_all(bind=engine)


# =========================
# 3. SECURITY CONFIG
# =========================
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# =========================
# 4. PASSWORD HELPERS
# =========================
def hash_password(password: str):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain, hashed):
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# =========================
# 5. JWT TOKEN
# =========================
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# =========================
# 6. REGISTER API
# =========================
@app.post("/register")
def register(username: str, password: str, db: Session = Depends(get_db)):


    user = db.query(User).filter(User.username == username).first()
    if user:
        raise HTTPException(status_code=400, detail="User already exists")


    if len(password) > 72:
        raise HTTPException(status_code=400, detail="Password too long")


    hashed_pw = hash_password(password)


    new_user = User(username=username, password=hashed_pw)


    db.add(new_user)
    db.commit()
    db.refresh(new_user)


    return {"message": "User registered successfully"}


# =========================
# 7. LOGIN API
# =========================
@app.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):


    user = db.query(User).filter(User.username == username).first()


    if not user:
        raise HTTPException(status_code=400, detail="Invalid username or password")


    if not verify_password(password, user.password):
        raise HTTPException(status_code=400, detail="Invalid username or password")


    token = create_access_token({"sub": user.username})


    return {
        "access_token": token,
        "token_type": "bearer"
    }


# =========================
# 8. GET CURRENT USER
# =========================
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")


        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")


        return username


    except:
        raise HTTPException(status_code=401, detail="Invalid token")


# =========================
# 9. PROTECTED ROUTE
# =========================
@app.get("/protected")
def protected_route(user: str = Depends(get_current_user)):
    return {
        "message": "You are authenticated",
        "user": user
    }
