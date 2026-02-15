from fastapi import FastAPI, Form, Depends, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database import engine, SessionLocal
import models
from auth import router as auth_router
from typing import Optional, List
import shutil
import os
import uuid
import json
import urllib.parse

# --- NEW IMPORTS FOR CLOUDINARY ---
import cloudinary
import cloudinary.uploader

# ---------------------------------------------------------
# 1. CLOUDINARY SETUP (PASTE YOUR KEYS HERE!) 
# ---------------------------------------------------------
cloudinary.config( 
  cloud_name = "YOUR_CLOUD_NAME", 
  api_key = "YOUR_API_KEY", 
  api_secret = "YOUR_API_SECRET",
  secure = True
)

# --- DATABASE SETUP ---
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Setup Image Storage (Fallback)
os.makedirs("static/images", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_router)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- HELPER 1: HANDLE IMAGE LISTS ---
def parse_images(image_data):
    if not image_data:
        return ["https://via.placeholder.com/600?text=No+Image"]
    try:
        return json.loads(image_data)
    except:
        return [image_data]

# --- HELPER 2: OPTIMIZE CLOUDINARY IMAGES ---
def optimize_url(url, width=500):
    if "cloudinary.com" not in url:
        return url 
    parts = url.split("/upload/")
    if len(parts) == 2:
        transformation = f"w_{width},c_fill,q_auto,f_auto"
        return f"{parts[0]}/upload/{transformation}/{parts[1]}"
    return url

# --- CSS & STYLING ---
HTML_HEAD = """
<head>
    <title>Vajrai Properties | Modern Living</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

    <style>
        body { font-family: 'Poppins', sans-serif; background-color: #f8f9fa; padding-bottom: 60px; }
        .navbar { background: white; box-shadow: 0 2px 10px rgba(0,0,0,0.1); padding: 10px 0; }
        .navbar-brand { font-weight: 700; color: #2c3e50; font-size: 1.4rem; }
        .nav-link { color: #555; font-weight: 500; margin-left: 15px; }
        
        .hero {
            background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url('https://images.unsplash.com/photo-1600596542815-2495db9b639e?ixlib=rb-4.0.3&auto=format&fit=crop&w=1600&q=80');
            background-size: cover; background-position: center; height: 40vh; min-height: 350px;
            display: flex; align-items: center; justify-content: center; text-align: center; color: white;
        }
        .hero h1 { font-size: 2.2rem; font-weight: 700; margin-bottom: 15px; }
        
        .option-card {
            background: rgba(255,255,255,0.15); backdrop-filter: blur(5px);
            border: 1px solid rgba(255,255,255,0.3); border-radius: 10px; padding: 15px; margin: 5px;
            color: white; transition: 0.3s; cursor: pointer; min-height: 120px;
            display: flex; flex-direction: column; justify-content: center;
        }
        .option-card:hover { background: rgba(255,255,255,0.25); transform: translateY(-3px); }
        .option-icon { font-size: 2rem; margin-bottom: 10px; color: #00d2ff; }
        
        .property-card { border: none; border-radius: 12px; overflow: hidden; background: white; box-shadow: 0 4px 10px rgba(0,0,0,0.05); transition: 0.3s; }
        .property-card:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.1); }
        .card-img-top { height: 200px; object-fit: cover; }
        
        .badge-category { position: absolute; top: 10px; left: 10px; padding: 4px 12px; border-radius: 20px; color: white; font-size: 0.75rem; text-transform: uppercase; z-index: 10; }
        .bg-rent { background-color: #17a2b8; }
        .bg-buy { background-color: #6610f2; }
        
        /* NEW: SOLD BADGE */
        .sold-overlay {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(255, 255, 255, 0.7); display: flex; align-items: center; justify-content: center;
            z-index: 5;
        }
        .sold-badge {
            background: #dc3545; color: white; font-weight: 800; padding: 10px 30px;
            font-size: 1.5rem; transform: rotate(-15deg); border: 4px solid white;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3); text-transform: uppercase;
        }
        
        .whatsapp-float { position: fixed; width: 55px; height: 55px; bottom: 80px; right: 20px; background-color: #25d366; color: #FFF; border-radius: 50px; text-align: center; font-size: 28px; z-index: 100; display: flex; align-items: center; justify-content: center; text-decoration: none; box-shadow: 2px 2px 10px rgba(0,0,0,0.2); }
    </style>
</head>
"""

# ---------------- HOME PAGE ----------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db), category: Optional[str] = None, location: Optional[str] = None):
    
    is_admin = request.cookies.get("admin_token") == "logged_in"
    
    query = db.query(models.Property)
    if category and category != "All":
        query = query.filter(models.Property.category == category)
    if location:
        query = query.filter(models.Property.location.contains(location))
    
    properties = query.all()

    cards_html = ""
    for p in properties:
        badge_color = "bg-buy" if p.category == "Buy" else "bg-rent"
        
        # Admin Controls
        admin_controls = ""
        if is_admin:
            admin_controls = f"""
            <div class="d-flex gap-2 mt-2">
                <a href="/edit-property/{p.id}" class="btn btn-warning btn-sm w-50"><i class="fas fa-edit"></i> Edit</a>
                <a href="/delete-property/{p.id}" class="btn btn-danger btn-sm w-50" onclick="return confirm('Delete?')"><i class="fas fa-trash"></i></a>
            </div>
            """

        images = parse_images(p.image)
        thumbnail = optimize_url(images[0], width=400)

        # SOLD LOGIC
        sold_overlay = ""
        if p.status == "Sold":
            sold_overlay = '<div class="sold-overlay"><div class="sold-badge">SOLD</div></div>'
        elif p.status == "Rented":
            sold_overlay = '<div class="sold-overlay"><div class="sold-badge bg-primary">RENTED</div></div>'

        cards_html += f"""
        <div class="col-md-4 mb-4">
            <div class="property-card">
                <div style="position:relative">
                    <span class="badge-category {badge_color}">{p.category}</span>
                    {sold_overlay}
                    <a href="/property/{p.id}">
                        <img src="{thumbnail}" class="card-img-top" alt="Property Image" loading="lazy">
                    </a>
                </div>
                <div class="card-body">
                    <h5 class="card-title text-truncate" style="font-size:1.1rem;">{p.title}</h5>
                    <p class="text-muted small mb-1"><i class="fas fa-map-marker-alt"></i> {p.location}</p>
                    <h5 class="text-success fw-bold">₹ {p.price}</h5>
                    
                    <a href="/property/{p.id}" class="btn btn-outline-primary w-100 btn-sm mt-2">View Details</a>
                    {admin_controls}
                </div>
            </div>
        </div>
        """

    if is_admin:
        nav_links = """
        <a class="nav-link fw-bold text-primary" href="/add-property"><i class="fas fa-plus-circle"></i> Add Property</a>
        <a class="nav-link text-danger" href="/logout">Logout</a>
        """
    else:
        nav_links = '<a class="nav-link" href="/admin">Admin Login</a>'

    return f"""
    <!DOCTYPE html>
    <html>
    {HTML_HEAD}
    <body>
        <nav class="navbar navbar-expand-lg">
            <div class="container">
                <a class="navbar-brand" href="/"><i class="fas fa-building"></i> Vajrai Properties</a>
                <div class="d-flex align-items-center">
                    <a class="nav-link" href="/">Home</a>
                    {nav_links}
                </div>
            </div>
        </nav>

        <div class="hero">
            <div class="container">
                <h1>Find Your Dream Home</h1>
                <div class="row justify-content-center mt-4">
                    <div class="col-4 col-md-3"><a href="/?category=Buy" style="text-decoration:none;"><div class="option-card"><i class="fas fa-home option-icon"></i><h3>BUY</h3></div></a></div>
                    <div class="col-4 col-md-3"><a href="https://wa.me/918999338010?text=I%20want%20to%20sell%20my%20property" target="_blank" style="text-decoration:none;"><div class="option-card"><i class="fas fa-hand-holding-usd option-icon"></i><h3>SELL</h3></div></a></div>
                    <div class="col-4 col-md-3"><a href="/?category=Rent" style="text-decoration:none;"><div class="option-card"><i class="fas fa-key option-icon"></i><h3>RENT</h3></div></a></div>
                </div>
            </div>
        </div>

        <div class="container mt-4">
            <div class="card p-3 shadow-sm mx-auto" style="max-width:800px; border-radius:10px;">
                <form action="/" method="get" class="row g-2">
                    <div class="col-md-3"><select name="category" class="form-select bg-light"><option value="All">All Types</option><option value="Buy">Buy</option><option value="Rent">Rent</option></select></div>
                    <div class="col-md-6"><input type="text" name="location" class="form-control bg-light" placeholder="Search Location (e.g. Virar)..."></div>
                    <div class="col-md-3"><button type="submit" class="btn btn-primary w-100">Search</button></div>
                </form>
            </div>
        </div>

        <div class="container mt-5">
            <h3 class="mb-4" style="font-weight:600;">Latest Properties</h3>
            <div class="row">{cards_html}</div>
        </div>

        <a href="https://wa.me/918999338010" class="whatsapp-float" target="_blank"><i class="fab fa-whatsapp"></i></a>
        <footer class="text-center pt-5 pb-4 text-muted"><p>© 2026 Vajrai Properties. All Rights Reserved.</p></footer>
    </body>
    </html>
    """

# ---------------- PROPERTY DETAILS ----------------
@app.get("/property/{pid}", response_class=HTMLResponse)
def property_details(pid: int, db: Session = Depends(get_db)):
    p = db.query(models.Property).filter(models.Property.id == pid).first()
    if not p: return HTMLResponse("<h1>Property Not Found</h1>", status_code=404)

    images = parse_images(p.image)
    carousel_items = ""
    for index, img_url in enumerate(images):
        active_class = "active" if index == 0 else ""
        optimized_img = optimize_url(img_url, width=800)
        carousel_items += f'<div class="carousel-item {active_class}"><img src="{optimized_img}" class="d-block w-100 rounded" style="height: 400px; object-fit: cover;" alt="Property Image"></div>'

    message = f"Hi, I am interested in {p.title} at {p.location}. Is it available?"
    wa_link = f"https://wa.me/918999338010?text={urllib.parse.quote(message)}"

    # Status Badge Logic
    status_badge = ""
    if p.status == "Sold":
        status_badge = '<span class="badge bg-danger ms-2">SOLD OUT</span>'
    elif p.status == "Rented":
        status_badge = '<span class="badge bg-primary ms-2">RENTED</span>'

    return f"""
    <!DOCTYPE html><html>{HTML_HEAD}<body>
        <nav class="navbar navbar-expand-lg"><div class="container"><a class="navbar-brand" href="/">Vajrai Properties</a><a href="/" class="btn btn-secondary btn-sm rounded-pill px-3">Back</a></div></nav>
        <div class="container mt-4">
            <div class="row">
                <div class="col-md-8 mb-4">
                    <div id="propCarousel" class="carousel slide" data-bs-ride="carousel">
                        <div class="carousel-inner">{carousel_items}</div>
                        <button class="carousel-control-prev" type="button" data-bs-target="#propCarousel" data-bs-slide="prev"><span class="carousel-control-prev-icon"></span></button>
                        <button class="carousel-control-next" type="button" data-bs-target="#propCarousel" data-bs-slide="next"><span class="carousel-control-next-icon"></span></button>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card shadow-sm p-4 border-0">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span class="badge bg-dark">{p.category}</span> {status_badge}
                        </div>
                        <h2>{p.title}</h2>
                        <h3 class="text-success fw-bold mb-3">₹ {p.price}</h3>
                        <p class="text-muted"><i class="fas fa-map-marker-alt"></i> {p.location}</p>
                        <hr>
                        <h5>Description</h5>
                        <p style="white-space: pre-line;">{p.description}</p>
                        <div class="d-none d-md-block">
                            <a href="{wa_link}" class="btn btn-success w-100 mb-2 btn-lg"><i class="fab fa-whatsapp"></i> Chat on WhatsApp</a>
                            <a href="tel:+918999338010" class="btn btn-outline-dark w-100"><i class="fas fa-phone"></i> Call Agent</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="d-md-none mobile-bottom-nav">
            <a href="tel:+918999338010" class="btn btn-outline-dark w-50 me-2"><i class="fas fa-phone"></i> Call</a>
            <a href="{wa_link}" class="btn btn-success w-50"><i class="fab fa-whatsapp"></i> WhatsApp</a>
        </div>
    </body></html>
    """

# ---------------- ADD PROPERTY ----------------
@app.get("/add-property", response_class=HTMLResponse)
def add_property_form(request: Request):
    if request.cookies.get("admin_token") != "logged_in": return RedirectResponse(url="/admin", status_code=303)
    return f"""
    <!DOCTYPE html><html>{HTML_HEAD}<body>
    <nav class="navbar"><div class="container"><a class="navbar-brand" href="/">Vajrai Properties</a></div></nav>
    <div class="container mt-5"><div class="card shadow p-4 mx-auto" style="max-width: 600px;">
    <h3 class="mb-3">Add New Property</h3>
    <form action="/add-property" method="post" enctype="multipart/form-data">
    <label class="form-label">Title</label><input name="title" class="form-control mb-3" required>
    <div class="row mb-3"><div class="col"><label class="form-label">Type</label><select name="category" class="form-select"><option value="Buy">Sell</option><option value="Rent">Rent</option></select></div>
    <div class="col"><label class="form-label">Price</label><input name="price" class="form-control" required></div></div>
    <label class="form-label">Location</label><input name="location" class="form-control mb-3" required>
    <label class="form-label">Description</label><textarea name="description" class="form-control mb-3" rows="4"></textarea>
    <label class="fw-bold form-label">Photos (Max 5)</label><input type="file" name="image_files" class="form-control mb-3" accept="image/*" multiple required>
    <button type="submit" class="btn btn-primary w-100">Submit</button>
    </form></div></div></body></html>
    """

@app.post("/add-property")
async def save_property(request: Request, title: str = Form(...), location: str = Form(...), price: str = Form(...), description: str = Form(...), category: str = Form(...), image_files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    if request.cookies.get("admin_token") != "logged_in": return RedirectResponse(url="/admin", status_code=303)
    uploaded_urls = []
    for file in image_files:
        try:
            res = cloudinary.uploader.upload(file.file)
            uploaded_urls.append(res.get("url"))
        except: pass
    # Default status is "Available"
    new_prop = models.Property(title=title, location=location, price=price, description=description, image=json.dumps(uploaded_urls), category=category, status="Available")
    db.add(new_prop)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

# ---------------- EDIT PROPERTY (WITH STATUS UPDATE) ----------------
@app.get("/edit-property/{pid}", response_class=HTMLResponse)
def edit_property_form(pid: int, request: Request, db: Session = Depends(get_db)):
    if request.cookies.get("admin_token") != "logged_in": return RedirectResponse(url="/admin", status_code=303)
    p = db.query(models.Property).filter(models.Property.id == pid).first()
    
    # Status Dropdown Logic
    options = ["Available", "Sold", "Rented"]
    status_options = ""
    for opt in options:
        selected = "selected" if p.status == opt else ""
        status_options += f'<option value="{opt}" {selected}>{opt}</option>'

    return f"""
    <!DOCTYPE html><html>{HTML_HEAD}<body>
    <div class="container mt-5"><div class="card shadow p-4 mx-auto" style="max-width: 600px;">
    <h3>Edit Property</h3>
    <form action="/edit-property/{pid}" method="post">
    <label>Title</label><input name="title" class="form-control mb-2" value="{p.title}" required>
    
    <div class="row mb-2">
        <div class="col"><label>Price</label><input name="price" class="form-control" value="{p.price}" required></div>
        <div class="col"><label class="fw-bold text-danger">Status</label><select name="status" class="form-select">{status_options}</select></div>
    </div>

    <label>Location</label><input name="location" class="form-control mb-2" value="{p.location}" required>
    <label>Description</label><textarea name="description" class="form-control mb-3" rows="5">{p.description}</textarea>
    <button type="submit" class="btn btn-warning w-100">Update</button>
    </form></div></div></body></html>
    """

@app.post("/edit-property/{pid}")
def update_property(pid: int, request: Request, title: str = Form(...), price: str = Form(...), location: str = Form(...), description: str = Form(...), status: str = Form(...), db: Session = Depends(get_db)):
    if request.cookies.get("admin_token") != "logged_in": return RedirectResponse(url="/admin", status_code=303)
    p = db.query(models.Property).filter(models.Property.id == pid).first()
    if p:
        p.title = title
        p.price = price
        p.location = location
        p.description = description
        p.status = status # Update status
        db.commit()
    return RedirectResponse(url=f"/property/{pid}", status_code=303)

# ---------------- DELETE & ADMIN ----------------
@app.get("/delete-property/{pid}")
def delete_property(pid: int, request: Request, db: Session = Depends(get_db)):
    if request.cookies.get("admin_token") != "logged_in": return RedirectResponse(url="/admin", status_code=303)
    prop = db.query(models.Property).filter(models.Property.id == pid).first()
    if prop: db.delete(prop); db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.get("/admin", response_class=HTMLResponse)
def admin_login(request: Request):
    error = request.query_params.get("error", "")
    return f"""
    <!DOCTYPE html><html>{HTML_HEAD}<body>
    <div class="container mt-5"><div class="card shadow p-4 mx-auto text-center" style="max-width:400px;">
    <h3>Admin Login</h3><p class="text-danger">{error}</p>
    <form action="/login" method="post">
    <input name="username" class="form-control mb-2" placeholder="User">
    <input type="password" name="password" class="form-control mb-2" placeholder="Pass">
    <button class="btn btn-primary w-100">Login</button>
    </form></div></div></body></html>
    """