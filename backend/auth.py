import jwt
import os
import bcrypt
from datetime import datetime, timedelta
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ.get("JWT_KEY")
ALGORITHM = os.environ.get("JWT_ALGORITHM")
security = HTTPBearer()

def verify_password(raw_password : str, hashed_password : str):
    return bcrypt.checkpw(raw_password.encode(), hashed_password.encode())

def get_password_hash(password : str):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def create_access_token(data : dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes= 60)
    to_encode.update({"exp" : expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm = ALGORITHM)
    return encoded_jwt

def verify_token(credentials : HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms= [ALGORITHM])
        if payload.get("role") != "admin":
            raise HTTPException(status_code= 403, detail= "Không đủ quyền hạn")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code= 401, detail= "Token đã hết hạn. Hãy đăng nhập lại")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code= 401, detail= "Token không hợp lệ")
    