from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
from pymongo import MongoClient
from bson import ObjectId
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()  # Loads variables from .env into environment

# MongoDB setup (adjust connection string as needed)
MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME")
client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
users_collection = db["users"]

# JWT Secret (use env variable in production)
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class User(BaseModel):
    name: str
    email: EmailStr
    password: str
    address: str

class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    address: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_user_by_email(email: str):
    return users_collection.find_one({"email": email})

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password):
    return pwd_context.hash(password)

@app.post("/register", response_model=UserOut)
def register(user: User):
    if get_user_by_email(user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pwd = hash_password(user.password)
    user_dict = user.dict()
    user_dict["password"] = hashed_pwd
    result = users_collection.insert_one(user_dict)
    return UserOut(
        id=str(result.inserted_id),
        name=user.name,
        email=user.email,
        address=user.address
    )

@app.post("/login", response_model=Token)
def login(user: UserLogin):
    db_user = get_user_by_email(user.email)
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token_data = {"sub": str(db_user["_id"]), "email": db_user["email"]}
    access_token = create_access_token(token_data)
    return {"access_token": access_token, "token_type": "bearer"}

# Dependency to get current user
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise credentials_exception
    return UserOut(
        id=str(user["_id"]),
        name=user["name"],
        email=user["email"],
        address=user["address"]
    )

@app.get("/me", response_model=UserOut)
def read_users_me(current_user: UserOut = Depends(get_current_user)):
    return current_user