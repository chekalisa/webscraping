from fastapi import FastAPI, HTTPException, status, Depends
from jose import JWTError, jwt
import requests
from pydantic import BaseModel
from datetime import datetime, timedelta

# Data models
class Item(BaseModel):
    id: int
    name: str
    description: str = None

class User(BaseModel):
    username: str

# Simulated in-memory database
fake_db_items = {}
fake_db_users = {}

app = FastAPI()

# JWT settings
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Function to create a JWT token
def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Endpoint to create a token
@app.get("/create-token")
def get_token():
    token_data = {"sub": "simple_user"}
    token = create_token(token_data)
    return {"access_token": token}

# Function to verify the token
def verify_token(token: str):
    try:
        # Decode and verify the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Dependency to protect routes
def get_current_user(token: str = Depends(lambda: None)):
    if token and token.startswith("Bearer "):
        token = token.split("Bearer ")[1]
        return verify_token(token)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No valid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.post("/items/", dependencies=[Depends(get_current_user)])
def create_item(item: Item):
    if item.id in fake_db_items:
        raise HTTPException(status_code=400, detail="Item already exists")
    fake_db_items[item.id] = item
    return {"message": "Item created successfully", "item": item}


@app.get("/items/{item_id}", dependencies=[Depends(get_current_user)])
def read_item(item_id: int):
    item = fake_db_items.get(item_id)
    if item:
        return item
    raise HTTPException(status_code=404, detail="Item not found")

# Health Check Endpoint
@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "ok"}

url = "https://impactco2.fr/api/v1/fruitsetlegumes?language=fr"

@app.get("/mydata", dependencies=[Depends(get_current_user)])
def get_data():
    response = requests.get(url)
    return response.json()
