from fastapi import FastAPI, Form, Depends, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database import engine, SessionLocal
import models
from auth import router as auth_router
import shutil, os

# ---------------- CREATE TABLES ----------------
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# ---------------- STATIC FOLDER ----------------
if not os.path.exists("static"):
    os.mkdir("static")

if not os.path.exists("static/uploads"):
    os.mkdir("static/uploads")

app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------------- INCLUDE LOGIN ROUTER ----------------
app.include_router(auth_router)

# ---------------- DB ----------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------- HOME PAGE ----------------
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <head>
    <title>Vajrai Properties | Virar-Vasai</title>
    </head>

    <body style="font-family:Arial;background:#f4f6f8">

    <h1 style="background:#0d6efd;color:white;padding:20px">
    🏠 Vajrai Properties – Virar Vasai
    </h1>

    <center>
    <h2>Find Your Dream Property</h2>
    <a href='/properties' style="padding:10px 20px;background:green;color:white;text-decoration:none">
    View Properties
    </a>
    <br><br>
    <a href='/login'>🔐 Admin Login</a>
    </center>

    </body>
    </html>
    """

# ---------------- ADD PROPERTY PAGE ----------------
@app.get("/add-property", response_class=HTMLResponse)
def add_property_form():
    return """
    <h2>🏠 Add Property</h2>

    <form action="/add-property" method="post" enctype="multipart/form-data">

    Title:<br>
    <input name="title"><br><br>

    Location:<br>
    <input name="location"><br><br>

    Price:<br>
    <input name="price"><br><br>

    Upload Image:<br>
    <input type="file" name="image"><br><br>

    Description:<br>
    <textarea name="description"></textarea><br><br>

    <button type="submit">Add Property</button>
    </form>

    <br><a href="/view-property">View All</a>
    """

# ---------------- SAVE PROPERTY ----------------
@app.post("/add-property", response_class=HTMLResponse)
def save_property(
    title: str = Form(...),
    location: str = Form(...),
    price: str = Form(...),
    description: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    filepath = f"static/uploads/{image.filename}"

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    image_url = "/" + filepath

    new_property = models.Property(
        title=title,
        location=location,
        price=price,
        description=description,
        image=image_url
    )

    db.add(new_property)
    db.commit()

    return """
    <h2>✅ Property Added Successfully</h2>
    <br>

    <a href='/add-property'>➕ Add Another Property</a><br><br>
    <a href='/view-property'>📋 View All Properties</a><br><br>
    <a href='/dashboard'>📊 Admin Dashboard</a><br><br>
    <a href='/'>🏠 Home Page</a>
    """


# ---------------- VIEW ADMIN ----------------
@app.get("/view-property", response_class=HTMLResponse)
def view_property(db: Session = Depends(get_db)):
    properties = db.query(models.Property).all()

    html = """
    <h1>🏢 Admin Properties</h1>

    <a href='/dashboard'>📊 Dashboard</a> |
    <a href='/add-property'>➕ Add Property</a> |
    <a href='/'>🏠 Website</a>

    <hr>
    """


    for p in properties:
        html += f"""
        <div style='border:1px solid gray;padding:10px;margin:10px;width:300px'>
        <img src='{p.image}' width='250'><br>
        <b>{p.title}</b><br>
        {p.location}<br>
        {p.price}<br>
        {p.description}<br><br>

        <a href='/delete-property/{p.id}' style='color:red'>Delete</a>
        </div>
        """

    html += "<br><a href='/add-property'>Add New</a>"
    return html

# ---------------- DELETE ----------------
@app.get("/delete-property/{pid}", response_class=HTMLResponse)
def delete_property(pid:int, db:Session=Depends(get_db)):
    prop = db.query(models.Property).filter(models.Property.id==pid).first()
    if prop:
        db.delete(prop)
        db.commit()
    return """
    <h2>❌ Property Deleted</h2><br>

    <a href='/view-property'>📋 Back to Properties</a><br><br>
    <a href='/add-property'>➕ Add Property</a><br><br>
    <a href='/dashboard'>📊 Dashboard</a><br><br>
    <a href='/'>🏠 Home</a>
    """


# ---------------- PUBLIC WEBSITE ----------------
@app.get("/properties", response_class=HTMLResponse)
def public_site(db: Session = Depends(get_db)):
    properties = db.query(models.Property).all()

    html = """
    <h1 style='background:#0d6efd;color:white;padding:15px'>
    🏠 Vajrai Properties - Virar Vasai
    </h1>
    """

    for p in properties:
        html += f"""
        <div style='border:1px solid gray;padding:15px;margin:20px;width:300px;display:inline-block'>
        <img src='{p.image}' width='100%'><br>
        <h3>{p.title}</h3>
        📍 {p.location}<br>
        💰 {p.price}<br><br>
        {p.description}<br><br>

        <a href='https://wa.me/917862895672?text=I want {p.title}'
        style='background:green;color:white;padding:10px;text-decoration:none'>
        WhatsApp
        </a>
        </div>
        """

    return html

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(db: Session = Depends(get_db)):
    total = db.query(models.Property).count()

    return f"""
    <h1>🏢 Vajrai Admin Dashboard</h1>
    <hr>

    <h3>Total Properties: {total}</h3><br>

    <a href='/add-property'>➕ Add Property</a><br><br>
    <a href='/view-property'>📋 View Properties</a><br><br>
    <a href='/properties'>🌐 Open Website</a><br><br>
    <a href='/'>🏠 Home</a>
    """
