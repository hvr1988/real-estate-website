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
        <title>Vajrai Properties | Modern Living</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>

    <nav class="navbar">
        <a href="/" class="brand">🏠 Vajrai Properties</a>
        <div class="nav-links">
            <a href="/">Home</a>
            <a href="/properties">Properties</a>
            <a href="/login">Admin</a>
        </div>
    </nav>

    <div class="hero">
        <h1>Find Your Dream Home.</h1>
        <p style="font-size: 1.2rem; opacity: 0.9;">Premium Real Estate in Virar, Vasai & Mumbai</p>
        
        <form action="/properties" method="get" class="hero-search">
            <input type="text" name="q" placeholder="Search by location (e.g. Virar West)...">
            <button type="submit">Search</button>
        </form>
    </div>

    <div class="section">
        <h2 style="font-size: 2.5rem; color: #0f172a;">Why Choose Us?</h2>
        <p style="color: #64748b;">We make finding your next home simple and stress-free.</p>
        
        <div class="features-container">
            <div class="feature-card">
                <span class="feature-icon">🤝</span>
                <h3>Trusted Agent</h3>
                <p>Over 100+ happy families have found their home through us in the last year.</p>
            </div>

            <div class="feature-card">
                <span class="feature-icon">💎</span>
                <h3>Best Deals</h3>
                <p>We negotiate directly with owners to get you the best market price.</p>
            </div>

            <div class="feature-card">
                <span class="feature-icon">📍</span>
                <h3>Prime Locations</h3>
                <p>All properties are located near Stations, Schools, and Markets.</p>
            </div>
        </div>
    </div>

    <div class="footer">
        <h3>Vajrai Properties</h3>
        <p>Office No 24, Galaxy Avenue, Virar West - 401303</p>
        <p>© 2026 All Rights Reserved</p>
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