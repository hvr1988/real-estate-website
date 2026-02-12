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
from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <head>
        <title>Vajrai Properties</title>
        <style>
            body {
                font-family: Arial;
                background:#f4f6f9;
                text-align:center;
                padding-top:80px;
            }
            .box{
                background:white;
                padding:40px;
                width:420px;
                margin:auto;
                border-radius:14px;
                box-shadow:0 0 25px rgba(0,0,0,0.15);
            }
            h1{color:#0d6efd}
            .btn{
                display:block;
                background:#0d6efd;
                color:white;
                padding:15px;
                margin-top:20px;
                text-decoration:none;
                border-radius:8px;
                font-size:18px;
            }
            .btn2{
                background:#198754;
            }
        </style>
    </head>
    <body>

        <div class="box">
            <h1>🏠 Vajrai Properties</h1>
            <h3>Virar • Vasai • Mumbai</h3>

            <a class="btn btn2" href="/properties">View Properties</a>
            <a class="btn" href="/login">Admin Login</a>
        </div>

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
def public_properties(db: Session = Depends(get_db)):

    properties = db.query(models.Property).all()

    html = """
    <html>
    <head>
    <title>Vajrai Properties | Virar-Vasai</title>

    <style>
    body{
        font-family:Arial;
        background:#f5f7fb;
        margin:0;
        padding:0;
    }

    .topbar{
        background:linear-gradient(90deg,#0d6efd,#0047ab);
        color:white;
        padding:18px;
        font-size:26px;
        font-weight:bold;
        text-align:center;
        letter-spacing:1px;
    }

    .container{
        padding:40px;
    }

    .card{
        background:white;
        width:320px;
        border-radius:12px;
        display:inline-block;
        margin:20px;
        box-shadow:0 6px 18px rgba(0,0,0,0.15);
        transition:0.3s;
        vertical-align:top;
    }

    .card:hover{
        transform:scale(1.03);
        box-shadow:0 10px 25px rgba(0,0,0,0.25);
    }

    .card img{
        width:100%;
        height:220px;
        object-fit:cover;
        border-radius:12px 12px 0 0;
    }

    .card-body{
        padding:15px;
    }

    .title{
        font-size:20px;
        font-weight:bold;
        margin-bottom:8px;
    }

    .loc{
        color:#666;
        margin-bottom:6px;
    }

    .price{
        color:#0d6efd;
        font-size:18px;
        font-weight:bold;
        margin-bottom:10px;
    }

    .desc{
        font-size:14px;
        margin-bottom:15px;
    }

    .btn{
        background:#25D366;
        color:white;
        padding:10px 18px;
        text-decoration:none;
        border-radius:6px;
        font-weight:bold;
        display:inline-block;
    }

    .footer{
        background:#111;
        color:#ccc;
        padding:30px;
        text-align:center;
        margin-top:40px;
        font-size:14px;
    }
    </style>
    </head>

    <body>

    <div class='topbar'>
    🏠 Vajrai Properties – Virar | Vasai
    </div>

    <div class='container'>
    """

    for p in properties:
        html += f"""
        <div class='card'>
            <img src='{p.image}'>

            <div class='card-body'>
                <div class='title'>{p.title}</div>
                <div class='loc'>📍 {p.location}</div>
                <div class='price'>💰 {p.price}</div>
                <div class='desc'>{p.description}</div>

                <a class='btn'
                href='https://api.whatsapp.com/send?phone=918999338010&text=I am interested in {p.title}'
                target='_blank'>
                WhatsApp Now
                </a>
            </div>
        </div>
        """

    html += """

    </div>

    <div class='footer'>
    © 2026 Vajrai Properties | Owner: Pankaj Nikam | 📞 8999338010  
    Serving Virar - Vasai Only
    </div>

    </body>
    </html>
    """

    return html
