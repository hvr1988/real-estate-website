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
    <!DOCTYPE html>
    <html>
    <head>
        <title>Vajrai Properties</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="/static/style.css">
        <style>
            /* Specific overrides for Home Page Hero */
            .hero {
                background: linear-gradient(rgba(15, 23, 42, 0.7), rgba(15, 23, 42, 0.7)), 
                            url("https://images.unsplash.com/photo-1560518883-ce09059eeffa");
                background-size: cover;
                height: 500px;
                color: white;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                text-align: center;
            }
            .hero h1 { font-size: 3rem; margin-bottom: 10px; }
            .section { padding: 60px 20px; text-align: center; }
            .btn-hero {
                background: #f97316;
                color: white;
                padding: 12px 30px;
                text-decoration: none;
                border-radius: 6px;
                font-weight: bold;
                margin-top: 20px;
                display: inline-block;
            }
        </style>
    </head>
    <body>

    <nav class="navbar">
        <a href="/" class="brand">🏠 Vajrai Properties</a>
        <div class="nav-links">
            <a href="/" class="active">Home</a>
            <a href="/properties">Properties</a>
            <a href="/login">Admin</a>
        </div>
    </nav>

    <div class="hero">
        <h1>Find Your Dream Property</h1>
        <p>Premium Flats & Commercial Spaces in Virar-Vasai</p>
        <a class="btn-hero" href="/properties">Browse Properties</a>
    </div>

    <div class="section">
        <h2>Why Choose Us?</h2>
        <div class="container">
            <div class="card" style="height:auto">
                <div class="card-body">
                    <h3>Trusted Agent</h3>
                    <p>100+ Happy Clients in your area.</p>
                </div>
            </div>
            <div class="card" style="height:auto">
                 <div class="card-body">
                    <h3>Best Deals</h3>
                    <p>Direct from owner listings available.</p>
                </div>
            </div>
            <div class="card" style="height:auto">
                 <div class="card-body">
                    <h3>Prime Locations</h3>
                    <p>Near Station, Schools & Markets.</p>
                </div>
            </div>
        </div>
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
# ---------------- PUBLIC WEBSITE ----------------
@app.get("/properties", response_class=HTMLResponse)
def public_properties(db: Session = Depends(get_db)):

    properties = db.query(models.Property).all()

    # START OF HTML
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Vajrai Properties | Search</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>

    <nav class="navbar">
        <a href="/" class="brand">🏠 Vajrai Properties</a>
        <div class="nav-links">
            <a href="/">Home</a>
            <a href="/properties" class="active">Properties</a>
            <a href="/login">Admin</a>
        </div>
    </nav>

    <div class="search-container">
        <h2>Find Your Perfect Home</h2>
        <input type="text" id="searchBox" class="search-box" 
               onkeyup="filterProperties()" 
               placeholder="🔍 Search by location, price, or title...">
    </div>

    <div class="container" id="propertyGrid">
    """

    # LOOP THROUGH PROPERTIES
    for p in properties:
        html += f"""
        <div class="card">
            <img src="{p.image}" alt="Property Image">
            <div class="card-body">
                <div class="title">{p.title}</div>
                <div class="loc">📍 {p.location}</div>
                <div class="price">💰 {p.price}</div>
                <div class="desc">{p.description}</div>
                
                <a class="btn-whatsapp" 
                   href="https://api.whatsapp.com/send?phone=918999338010&text=Hi, I am interested in {p.title}" 
                   target="_blank">
                   WhatsApp Now
                </a>
            </div>
        </div>
        """

    # END OF HTML + JAVASCRIPT FOR SEARCH
    html += """
    </div>

    <script>
    function filterProperties() {
        // 1. Get the search text
        let input = document.getElementById('searchBox');
        let filter = input.value.toUpperCase();
        
        // 2. Get all cards
        let container = document.getElementById('propertyGrid');
        let cards = container.getElementsByClassName('card');

        // 3. Loop through cards and hide those that don't match
        for (let i = 0; i < cards.length; i++) {
            let title = cards[i].getElementsByClassName("title")[0];
            let loc = cards[i].getElementsByClassName("loc")[0];
            let price = cards[i].getElementsByClassName("price")[0];
            
            // Combine text to search in Title, Location AND Price
            let txtValue = title.textContent + " " + loc.textContent + " " + price.textContent;
            
            if (txtValue.toUpperCase().indexOf(filter) > -1) {
                cards[i].style.display = "";
            } else {
                cards[i].style.display = "none";
            }
        }
    }
    </script>

    </body>
    </html>
    """

    return html