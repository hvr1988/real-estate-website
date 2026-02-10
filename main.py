from fastapi import FastAPI, Form, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from database import engine, SessionLocal
import models
from auth import router as auth_router # Moved import to top for better style
from fastapi import File, UploadFile
import shutil
import os

app = FastAPI()

# Create tables
models.Base.metadata.create_all(bind=engine)

# create upload folder if not exists
if not os.path.exists("static"):
    os.mkdir("static")

if not os.path.exists("static/uploads"):
    os.mkdir("static/uploads")

from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")


# Include the auth router
app.include_router(auth_router)

# DB connection dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------- HOME PAGE ----------------

from fastapi import Request
from fastapi.templating import Jinja2Templates

import os
templates = Jinja2Templates(directory="templates") if os.path.exists("templates") else None


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    if templates:
        return templates.TemplateResponse("index.html", {"request": request})
    else:
        return """
        <h2>🏠 Vajrai Properties Running</h2>
        <a href='/properties'>View Properties</a><br>
        <a href='/login'>Admin Login</a>
        """


# ---------------- ADD PROPERTY PAGE (FORM) ----------------

# ---------------- ADMIN ADD PROPERTY PAGE ----------------
@app.get("/add-property", response_class=HTMLResponse)
def add_property_form():

    return """
    <html>
    <head>
    <title>Admin Panel - Vajrai Properties</title>

    <style>
    body{font-family:Arial;background:#f4f6f8;padding:40px}
    h2{color:#0d6efd}
    input,textarea{width:300px;padding:8px;margin:8px}
    button{background:#0d6efd;color:white;padding:10px 20px;border:none}
    a{display:block;margin-top:20px}
    </style>
    </head>

    <body>

    <h2>🏠 Admin Panel - Add Property</h2>

    <form action="/add-property" method="post" enctype="multipart/form-data">

    Title:<br>
    <input name="title" placeholder="1BHK in Virar"><br>

    Location:<br>
    <input name="location" placeholder="Virar West"><br>

    Price:<br>
    <input name="price" placeholder="35 Lakh"><br>

    Image Upload:<br>
    <input type="file" name="image"><br>

    Description:<br>
    <textarea name="description" placeholder="Near station"></textarea><br><br>

    <button type="submit">Add Property</button>

    </form>

    <a href="/view-property">📋 View All Properties</a>
    <a href="/">🏠 Back to Website</a>

    </body>
    </html>
    """



# ---------------- SAVE PROPERTY (POST) ----------------

@app.post("/add-property", response_class=HTMLResponse)
def save_property(
    title: str = Form(...), 
    location: str = Form(...),
    price: str = Form(...), 
    description: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    # Save uploaded file
    file_path = f"static/uploads/{image.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    image_url = "/" + file_path.replace("\\", "/")

    new_property = models.Property(
        title=title,
        location=location,
        price=price,
        description=description,
        image=image_url
    )

    db.add(new_property)
    db.commit()

    return f"<h3>Property '{title}' Added Successfully</h3><br><a href='/view-property'>View All</a>"

# ---------------- VIEW ALL PROPERTIES ----------------

@app.get("/view-property", response_class=HTMLResponse)
def view_property(db: Session = Depends(get_db)):

    properties = db.query(models.Property).all()

    html = """
    <h1>🏢 All Properties (Admin)</h1>
    <a href='/add-property'>➕ Add New</a> |
    <a href='/'>🏠 Website</a>
    <hr>
    """

    for p in properties:
        html += f"""
        <div style='border:1px solid gray;
        padding:15px;margin:15px;width:300px;
        display:inline-block;background:#fff;
        box-shadow:0px 0px 8px gray'>

        <img src='{p.image}' width='100%'><br><br>

        <h3>{p.title}</h3>
        📍 {p.location}<br>
        💰 {p.price}<br><br>

        {p.description}<br><br>

        
        <a href='https://api.whatsapp.com/send?phone=917862895672&text=I am interested in {p.title}'
        style='background:green;color:white;
        padding:8px 12px;text-decoration:none'>
        WhatsApp Client
        </a>
        <br><br>

        <a href='/delete-property/{p.id}'
        style='color:red;font-weight:bold'>
        ❌ Delete
        </a>

        </div>
        """

    return html


# ---------------- DELETE PROPERTY ----------------
@app.get("/delete-property/{pid}", response_class=HTMLResponse)
def delete_property(pid: int, db: Session = Depends(get_db)):
    property_to_delete = db.query(models.Property).filter(models.Property.id == pid).first()

    if property_to_delete:
        db.delete(property_to_delete)
        db.commit()
        return "<h3>Property Deleted</h3><br><a href='/view-property'>Back to List</a>"
    
    return "<h3>Property Not Found</h3><br><a href='/view-property'>Back to List</a>"

# ---------------- PUBLIC WEBSITE ----------------
@app.get("/properties", response_class=HTMLResponse)
def public_properties(db: Session = Depends(get_db)):

    properties = db.query(models.Property).all()

    html = """
    <html>
    <head>
    <title>Vajrai Properties | Virar-Vasai Real Estate</title>
    </head>

    <body style="font-family:Arial;background:#f4f6f8">

    <h1 style="background:#0d6efd;color:white;padding:15px">
    🏠 Dream Properties
    </h1>

    <center>
    <h2>Find Your Perfect Home</h2>
    </center>
    <hr>
    """

    for p in properties:
        html += f"""
        <div style='background:white;border-radius:10px;
        padding:15px;margin:20px;box-shadow:0px 0px 10px gray;
        width:300px;display:inline-block'>

        <img src='{p.image}' width='100%' style='border-radius:10px'><br><br>

        <h3>{p.title}</h3>
        📍 {p.location}<br>
        💰 <b>{p.price}</b><br><br>

        {p.description}<br><br>

        <a href='https://api.whatsapp.com/send?phone=917862895672&text=I am interested in {p.title}'
        style='background:green;color:white;padding:10px;
        text-decoration:none;border-radius:5px'>
        📞 WhatsApp Now
        </a>

        </div>
        """

    html += "</body></html>"
    return html