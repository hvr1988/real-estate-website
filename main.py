from fastapi import FastAPI, Form, Depends, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database import engine, SessionLocal
import models
from auth import router as auth_router
from typing import Optional
import shutil
import os
import uuid

# --- DATABASE SETUP ---
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# ---------------------------------------------------------
# 1. SETUP IMAGE STORAGE (Crucial for File Uploads)
# ---------------------------------------------------------
# Create a folder named 'static/images' if it doesn't exist
os.makedirs("static/images", exist_ok=True)

# Mount the folder so the browser can see the images
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_router)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- CSS & STYLING ---
HTML_HEAD = """
<head>
    <title>Vajrai Properties | Modern Living</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    
    <style>
        body { font-family: 'Poppins', sans-serif; background-color: #f8f9fa; }
        .navbar { background: white; box-shadow: 0 2px 10px rgba(0,0,0,0.1); padding: 15px 0; }
        .navbar-brand { font-weight: 700; color: #2c3e50; font-size: 1.5rem; }
        .nav-link { color: #555; font-weight: 500; margin-left: 20px; }
        .nav-link:hover { color: #007bff; }
        
        .hero {
            background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url('https://images.unsplash.com/photo-1600596542815-2495db9b639e?ixlib=rb-4.0.3&auto=format&fit=crop&w=1600&q=80');
            background-size: cover; background-position: center; height: 75vh;
            display: flex; align-items: center; justify-content: center; text-align: center; color: white;
        }
        .hero h1 { font-size: 3.5rem; font-weight: 700; margin-bottom: 10px; }
        
        .option-card {
            background: rgba(255,255,255,0.1); backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 15px; padding: 30px; margin: 10px;
            color: white; transition: 0.3s; cursor: pointer;
            min-height: 180px; display: flex; flex-direction: column; justify-content: center;
        }
        .option-card:hover { background: rgba(255,255,255,0.2); transform: translateY(-5px); }
        .option-icon { font-size: 3rem; margin-bottom: 15px; color: #00d2ff; }
        
        .property-card { border: none; border-radius: 15px; overflow: hidden; background: white; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
        .card-img-top { height: 200px; object-fit: cover; }
        .badge-category { position: absolute; top: 10px; left: 10px; padding: 5px 15px; border-radius: 20px; color: white; font-size: 0.8rem; text-transform: uppercase; }
        .bg-rent { background-color: #17a2b8; }
        .bg-buy { background-color: #6610f2; }
        
        .whatsapp-float { position: fixed; width: 60px; height: 60px; bottom: 40px; right: 40px; background-color: #25d366; color: #FFF; border-radius: 50px; text-align: center; font-size: 30px; z-index: 100; display: flex; align-items: center; justify-content: center; text-decoration: none; }
        
        footer { background: #2c3e50; color: white; padding: 40px 0; margin-top: 50px; }
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
        
        delete_btn = ""
        if is_admin:
            delete_btn = f'<a href="/delete-property/{p.id}" class="text-danger small mt-2 d-block text-center fw-bold" onclick="return confirm(\'Delete?\')">❌ Admin: Delete</a>'

        # If the image path is missing, use a placeholder
        img_src = p.image if p.image else "https://via.placeholder.com/300?text=No+Image"

        cards_html += f"""
        <div class="col-md-4 mb-4">
            <div class="property-card">
                <div style="position:relative">
                    <span class="badge-category {badge_color}">{p.category}</span>
                    <img src="{img_src}" class="card-img-top" alt="Property Image">
                </div>
                <div class="card-body">
                    <h5 class="card-title">{p.title}</h5>
                    <p class="text-muted"><i class="fas fa-map-marker-alt"></i> {p.location}</p>
                    <p class="fw-bold text-success">₹ {p.price}</p>
                    <p class="card-text">{p.description[:100]}...</p>
                    {delete_btn}
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
                <p class="lead mb-5">Premium Real Estate in Virar, Vasai & Mumbai</p>
                
                <div class="row justify-content-center">
                    <div class="col-md-3">
                        <a href="/?category=Buy" style="text-decoration:none;">
                            <div class="option-card">
                                <i class="fas fa-home option-icon"></i>
                                <h3>BUY</h3>
                                <p class="small">Browse Homes for Sale</p>
                            </div>
                        </a>
                    </div>
                    <div class="col-md-3">
                        <a href="https://wa.me/918999338010?text=I%20want%20to%20sell%20my%20property" target="_blank" style="text-decoration:none;">
                            <div class="option-card">
                                <i class="fas fa-hand-holding-usd option-icon"></i>
                                <h3>SELL</h3>
                                <p class="small">List Your Property</p>
                            </div>
                        </a>
                    </div>
                    <div class="col-md-3">
                        <a href="/?category=Rent" style="text-decoration:none;">
                            <div class="option-card">
                                <i class="fas fa-key option-icon"></i>
                                <h3>RENT</h3>
                                <p class="small">Find Rental Homes</p>
                            </div>
                        </a>
                    </div>
                </div>
            </div>
        </div>

        <div class="container mt-5">
            <h2 class="text-center mb-4">Available Properties</h2>
            {f'<div class="text-center mb-4"><a href="/" class="btn btn-secondary btn-sm">Show All Properties</a></div>' if category else ''}
            <div class="row">
                {cards_html}
            </div>
        </div>

        <a href="https://wa.me/918999338010" class="whatsapp-float" target="_blank">
            <i class="fab fa-whatsapp"></i>
        </a>

        <footer class="text-center">
            <p>© 2026 Vajrai Properties. All Rights Reserved.</p>
        </footer>
    </body>
    </html>
    """

# ---------------- ADD PROPERTY PAGE (With File Upload) ----------------
@app.get("/add-property", response_class=HTMLResponse)
def add_property_form(request: Request):
    if request.cookies.get("admin_token") != "logged_in":
        return RedirectResponse(url="/admin?error=Login Required to Add Property", status_code=303)

    return f"""
    <!DOCTYPE html>
    <html>
    {HTML_HEAD}
    <body style="background-color: #f0f2f5;">
        <nav class="navbar navbar-expand-lg" style="background:white;">
            <div class="container">
                <a class="navbar-brand" href="/">Vajrai Properties</a>
                <a href="/" class="btn btn-secondary rounded-pill px-3">Back</a>
            </div>
        </nav>

        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="card shadow-lg p-4">
                        <h2 class="text-center mb-4">Post a Property</h2>
                        
                        <form action="/add-property" method="post" enctype="multipart/form-data">
                            
                            <div class="mb-3">
                                <label>Title</label>
                                <input name="title" class="form-control" required>
                            </div>
                            <div class="row mb-3">
                                <div class="col">
                                    <label>Type</label>
                                    <select name="category" class="form-select">
                                        <option value="Buy">Sell (For Sale)</option>
                                        <option value="Rent">Rent (To Let)</option>
                                    </select>
                                </div>
                                <div class="col">
                                    <label>Price</label>
                                    <input name="price" class="form-control" required>
                                </div>
                            </div>
                            <div class="mb-3">
                                <label>Location</label>
                                <input name="location" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label>Description</label>
                                <textarea name="description" class="form-control" rows="3"></textarea>
                            </div>
                            
                            <div class="mb-3">
                                <label class="fw-bold">Upload Property Photo</label>
                                <input type="file" name="image_file" class="form-control" accept="image/*" required>
                                <small class="text-muted">Select a photo from your computer</small>
                            </div>
                            
                            <button type="submit" class="btn btn-primary w-100">Submit Property</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

# ---------------- SAVE PROPERTY LOGIC (Handles File Upload) ----------------
@app.post("/add-property", response_class=HTMLResponse)
async def save_property(
    request: Request,
    title: str = Form(...), location: str = Form(...),
    price: str = Form(...), description: str = Form(...),
    category: str = Form(...),
    image_file: UploadFile = File(...), # Receives the file
    db: Session = Depends(get_db)
):
    if request.cookies.get("admin_token") != "logged_in":
        return RedirectResponse(url="/admin", status_code=303)

    # 1. Generate a unique filename to prevent overwriting
    unique_filename = f"{uuid.uuid4()}_{image_file.filename}"
    file_path = f"static/images/{unique_filename}"
    
    # 2. Save the file to the "static/images" folder
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image_file.file, buffer)
    
    # 3. Create the URL for the database (e.g., /static/images/photo.jpg)
    image_url = f"/static/images/{unique_filename}"

    # 4. Save to Database
    new_property = models.Property(
        title=title, location=location, price=price,
        description=description, image=image_url, category=category 
    )
    db.add(new_property)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

# ---------------- DELETE LOGIC ----------------
@app.get("/delete-property/{pid}")
def delete_property(pid: int, request: Request, db: Session = Depends(get_db)):
    if request.cookies.get("admin_token") != "logged_in":
        return RedirectResponse(url="/admin", status_code=303)
        
    prop = db.query(models.Property).filter(models.Property.id == pid).first()
    if prop:
        db.delete(prop)
        db.commit()
    return RedirectResponse(url="/", status_code=303)

# ---------------- ADMIN LOGIN ----------------
@app.get("/admin", response_class=HTMLResponse)
def admin_login_page(request: Request):
    error_msg = request.query_params.get("error", "")
    error_html = f'<div class="alert alert-danger">{error_msg}</div>' if error_msg else ""

    return f"""
    <!DOCTYPE html>
    <html>
    {HTML_HEAD}
    <body style="background-color: #f0f2f5;">
        <nav class="navbar navbar-expand-lg" style="background:white;">
            <div class="container">
                <a class="navbar-brand" href="/">Vajrai Properties</a>
                <a href="/" class="btn btn-secondary rounded-pill px-3">Back</a>
            </div>
        </nav>

        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-4">
                    <div class="card shadow p-4 text-center">
                        <h3 class="mb-3">Admin Login</h3>
                        {error_html}
                        <form action="/login" method="post">
                            <div class="mb-3 text-start">
                                <label>Username</label>
                                <input name="username" class="form-control" required>
                            </div>
                            <div class="mb-3 text-start">
                                <label>Password</label>
                                <input type="password" name="password" class="form-control" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">Login</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """