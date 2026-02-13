from fastapi import FastAPI, Form, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from database import engine, SessionLocal
import models
from auth import router as auth_router
from typing import Optional

# --- DATABASE SETUP ---
models.Base.metadata.create_all(bind=engine)

app = FastAPI()
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
        .btn-primary { background-color: #007bff; border: none; padding: 10px 25px; border-radius: 30px; }
        
        /* Hero */
        .hero {
            background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url('https://images.unsplash.com/photo-1600596542815-2495db9b639e?ixlib=rb-4.0.3&auto=format&fit=crop&w=1600&q=80');
            background-size: cover; background-position: center; height: 60vh;
            display: flex; align-items: center; justify-content: center; text-align: center; color: white;
        }
        .hero h1 { font-size: 3.5rem; font-weight: 700; margin-bottom: 20px; }
        
        /* Cards */
        .property-card { border: none; border-radius: 15px; overflow: hidden; background: white; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
        .card-img-top { height: 200px; object-fit: cover; }
        .badge-category { position: absolute; top: 10px; left: 10px; padding: 5px 15px; border-radius: 20px; color: white; font-size: 0.8rem; text-transform: uppercase; }
        .bg-rent { background-color: #17a2b8; }
        .bg-buy { background-color: #6610f2; }
        
        .whatsapp-float { position: fixed; width: 60px; height: 60px; bottom: 40px; right: 40px; background-color: #25d366; color: #FFF; border-radius: 50px; text-align: center; font-size: 30px; z-index: 100; display: flex; align-items: center; justify-content: center; text-decoration: none; }
    </style>
</head>
"""

# ---------------- HOME PAGE ----------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db), category: Optional[str] = None, location: Optional[str] = None):
    
    # 🔍 Check if Admin is logged in (Look for Cookie)
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
        
        # 🔒 Only show DELETE button if Admin
        delete_btn = ""
        if is_admin:
            delete_btn = f'<a href="/delete-property/{p.id}" class="text-danger small mt-2 d-block text-center fw-bold" onclick="return confirm(\'Delete this property?\')">❌ Admin: Delete</a>'

        cards_html += f"""
        <div class="col-md-4 mb-4">
            <div class="property-card">
                <div style="position:relative">
                    <span class="badge-category {badge_color}">{p.category}</span>
                    <img src="{p.image}" class="card-img-top" alt="Property Image">
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

    # Admin Link Logic (Show Login or Logout)
    if is_admin:
        admin_link = '<a class="nav-link text-danger fw-bold" href="/logout">Logout</a>'
    else:
        admin_link = '<a class="nav-link" href="/admin">Admin Login</a>'

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
                    <a class="nav-link" href="/add-property">Sell</a>
                    {admin_link}
                </div>
            </div>
        </nav>

        <div class="hero">
            <div class="container">
                <h1>Find Your Dream Home</h1>
                <p class="lead">Premium Real Estate in Virar, Vasai & Mumbai</p>
                
                <div class="card p-3 shadow-lg mx-auto" style="max-width:800px">
                    <form action="/" method="get" class="row g-2">
                        <div class="col-md-4">
                            <select name="category" class="form-select">
                                <option value="All">Show All</option>
                                <option value="Buy">Buy</option>
                                <option value="Rent">Rent</option>
                            </select>
                        </div>
                        <div class="col-md-5">
                            <input type="text" name="location" class="form-control" placeholder="Search Location...">
                        </div>
                        <div class="col-md-3">
                            <button type="submit" class="btn btn-primary w-100">Search</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>

        <div class="container mt-5">
            <h2 class="text-center mb-4">Latest Properties</h2>
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

# ---------------- ADMIN LOGIN PAGE ----------------
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

# ---------------- ADD PROPERTY PAGE ----------------
@app.get("/add-property", response_class=HTMLResponse)
def add_property_form():
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
                        <form action="/add-property" method="post">
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
                                <label>Image URL</label>
                                <input name="image" class="form-control">
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

# ---------------- SAVE PROPERTY LOGIC ----------------
@app.post("/add-property", response_class=HTMLResponse)
def save_property(
    title: str = Form(...), location: str = Form(...),
    price: str = Form(...), description: str = Form(...),
    image: str = Form(...), category: str = Form(...),
    db: Session = Depends(get_db)
):
    new_property = models.Property(
        title=title, location=location, price=price,
        description=description, image=image, category=category 
    )
    db.add(new_property)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

# ---------------- DELETE LOGIC ----------------
@app.get("/delete-property/{pid}")
def delete_property(pid: int, db: Session = Depends(get_db)):
    prop = db.query(models.Property).filter(models.Property.id == pid).first()
    if prop:
        db.delete(prop)
        db.commit()
    return RedirectResponse(url="/", status_code=303)