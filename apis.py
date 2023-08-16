from fastapi import FastAPI, HTTPException, Depends, File, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List, Optional
import csv

app = FastAPI()

# Mock database to store users and products
class Database:
    def __init__(self):
        self.users = []
        self.products = []

db = Database()

# Authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password

class Product:
    def __init__(self, name, barcode, brand, description, price, available):
        self.name = name
        self.barcode = barcode
        self.brand = brand
        self.description = description
        self.price = price
        self.available = available

def get_user(username: str):
    for user in db.users:
        if user.username == username:
            return user


def get_current_user(token: str = Depends(oauth2_scheme)):
    user = get_user(username=token)
    if user:
        return user
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/register/")
async def register_user(username: str, password: str):
    db.users.append(User(username=username, password=password))
    return {"message": "User registered successfully"}


@app.post("/token/")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(username=form_data.username)
    if user and user.password == form_data.password:
        return {"access_token": user.username, "token_type": "bearer"}
    else:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

@app.post("/upload/")
async def upload_csv(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    content = await file.read()
    decoded_content = content.decode("utf-8")
    csv_reader = csv.reader(decoded_content.splitlines(), delimiter=',')
    for row in csv_reader:
        db.products.append(Product(*row))
    return {"message": "CSV file uploaded successfully"}


@app.post("/review/")
async def review_product(product_id: int, rating: int, current_user: User = Depends(get_current_user)):
    if product_id < 1 or product_id > len(db.products):
        raise HTTPException(status_code=400, detail="Invalid product ID")
    db.products[product_id - 1].rating = rating
    return {"message": "Review submitted successfully"}


@app.get("/products/")
async def get_products(page: int = 1, items_per_page: int = 5, sort_by: Optional[str] = None):
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    sorted_products = sorted(db.products, key=lambda x: x.rating if x.rating else 0, reverse=True)
    if sort_by == "name":
        sorted_products = sorted(db.products, key=lambda x: x.name)
    elif sort_by == "price":
        sorted_products = sorted(db.products, key=lambda x: x.price)
    return sorted_products[start_idx:end_idx]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
