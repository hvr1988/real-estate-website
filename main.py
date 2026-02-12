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
    <title>Vajrai Properties</title>

    <style>
    body{
        font-family:Arial;
        margin:0;
        background:#f4f6fb;
    }

    .topbar{
        background:linear-gradient(90deg,#0d6efd,#0047ab);
        color:white;
        padding:18px;
        font-size:26px;
        text-align:center;
        font-weight:bold;
    }

    .hero{
        text-align:center;
        padding:60px 20px;
    }

    .hero h1{
        font-size:34px;
        color:#333;
    }

    .btn{
        display:inline-block;
        padding:15px 25px;
        margin:10px;
        font-size:18px;
        border-radius:8px;
        text-decoration:none;
        color:white;
        font-weight:bold;
    }

    .view{background:#198754;}
    .login{background:#0d6efd;}

    .section{
        padding:50px;
        text-align:center;
    }

    .card{
        display:inline-block;
        width:260px;
        background:white;
        padding:20px;
        margin:15px;
        border-radius:10px;
        box-shadow:0 5px 15px rgba(0,0,0,0.15);
    }

    .footer{
        background:#111;
        color:#ccc;
        text-align:center;
        padding:30px;
        margin-top:40px;
    }
    </style>
    </head>

    <body>

    <div class="topbar">
    🏠 Vajrai Properties – Virar | Vasai | Mumbai
    </div>

    <div class="hero">
        <h1>Find Your Dream Property</h1>

        <a class="btn view" href="/properties">View Properties</a>
        <a class="btn login" href="/login">Admin Login</a>
    </div>

    <div class="section">
        <h2>Why Choose Us</h2>

        <div class="card">
        <h3>Trusted Agent</h3>
        100+ Happy Clients in Virar-Vasai
        </div>

        <div class="card">
        <h3>Best Deals</h3>
        1RK to Luxury Villas Available
        </div>

        <div class="card">
        <h3>Prime Locations</h3>
        Near Station, School & Market
        </div>
    </div>

    <div class="section">
        <h2>Contact Us</h2>
        📍 Office No 24, Galaxy Avenue, Virar West<br><br>
        📞 8999338010<br><br>
        🟢 WhatsApp Available 24/7
    </div>

    <div class="footer">
    © 2026 Vajrai Properties | Owner: Pankaj Nikam<br>
    Serving Virar - Vasai - Mumbai
    </div>

    </body>
    </html>
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
