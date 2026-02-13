from fastapi import FastAPI, Form, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import text  # Required for the database fix
from database import engine, SessionLocal
import models
from auth import router as auth_router
from typing import Optional

# --- DATABASE SETUP ---
# creating tables (this will auto-create tables if they don't exist)
models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(auth_router)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------------------
# 🛠️ DATABASE REPAIR ROUTE (Run this once)
# ---------------------------------------------------------
@app.get("/fix-db", response_class=HTMLResponse)
def fix_database(db: Session = Depends(get_db)):
    try:
        # 1. Drop the old table
        db.execute(text("DROP TABLE IF EXISTS properties;"))
        db.commit()
        
        # 2. Recreate the table with the new 'category' column
        models.Base.metadata.create_all(bind=engine)
        
        return """
        <div style="padding:50px; text-align:center; font-family:sans-serif;">
            <h1 style="color:green;">✅ Success! Database Repaired.</h1>
            <p>The old table was deleted and a new one with the 'category' column was created.</p>
            <br>
            <a href="/" style="background:blue; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;">Go to Home Page</a>
        </div>
        """
    except Exception as e:
        return f"<h1>❌ Error: {e}</h1>"

# --- CSS & STYLING (Professional Theme) ---
HTML_HEAD = """
<head>
    <title>Dream Homes | Real Estate</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    
    <style>
        body { font-family: 'Poppins', sans-serif; background-color: #f8f9fa; }
        
        /* Navbar */
        .navbar { background: white; box-shadow: 0 2px 10px rgba(0,0,0,0.1); padding: 15px 0; }
        .navbar-brand { font-weight: 700; color: #2c3e50; font-size: 1.5rem; }
        .nav-link { color: #555; font-weight: 500; margin-left: 20px; }
        .nav-link:hover { color: #007bff; }
        .btn-primary { background-color: #007bff; border: none; padding: 10px 25px; border-radius: 30px; }

        /* Hero Section */
        .hero {
            background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url('https://images.unsplash.com/photo-1600596542815-2495db9b639e?ixlib=rb-4.0.3&auto=format&fit=crop&w=1600&q=80');
            background-size: cover;
            background-position: center;
            height: 60vh;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            color: white;
        }
        .hero h1 { font-size: 3.5rem; font-weight: 700; margin-bottom: 20px; }
        
        /* Search Box */
        .search-box {
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            max-width: 800px;
            width: 90%;
            margin: 0 auto;
        }

        /* Property Cards */
        .property-card {
            border: none;
            border-radius: 15px;
            overflow: hidden;
            transition: transform 0.3s;
            background: white;
            box-shadow: 0 5px 15px rgba(0,0,0,0.05);
            height: 100%;
        }
        .property-card:hover { transform: translateY(-5px); box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
        .card-img-top { height: 200px; object-fit: cover; }
        .price-tag { color: #28a745; font-weight: 700; font-size: 1.2rem; }
        .badge-category { position: absolute; top: 10px; left: 10px; padding: 5px 15px; border-radius: 20px; color: white; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; }
        .bg-rent { background-color: #17a2b8; }
        .bg-buy { background-color: #6610f2; }

        /* WhatsApp Button */
        .whatsapp-float {
            position: fixed;
            width: 60px;
            height: 60px;
            bottom: 40px;
            right: 40px;
            background-color: #25d366;
            color: #FFF;
            border-radius: 50px;
            text-align: center;
            font-size: 30px;
            box-shadow: 2px 2px 3px #999;
            z-index: 100;
            display: flex;
            align-items: center;
            justify-content: center;
            text-decoration: none;
        }
        .whatsapp-float:hover { background-color: #20ba5a; color: white; }

        /* Footer */
        footer { background: #2c3e50; color: white; padding: 40px 0; margin-top: 50px; }
    </style>
</head>
"""

# ---------------- HOME PAGE (HERO + FILTERS) ----------------
@app.get("/", response_class=HTMLResponse)
def home(db: Session = Depends(get_db), category: Optional[str] = None, location: Optional[str] = None):
    
    # Filter Logic
    query = db.query(models.Property)
    if category and category != "All":
        query = query.filter(models.Property.category == category)
    if location:
        query = query.filter(models.Property.location.contains(location))
    
    properties = query.all()

    # Generate Property Cards HTML
    cards_html = ""
    for p in properties:
        badge_color = "bg-buy" if p.category == "Buy" else "bg-rent"
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
                    <p class="price-tag">₹ {p.price}</p>
                    <p class="card-text">{p.description[:100]}...</p>
                    <a href="#" class="btn btn-outline-primary w-100">View Details</a>
                    
                    <a href="/delete-property/{p.id}" class="text-danger small mt-2 d-block text-center">Admin: Delete</a>
                </div>
            </div>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    {HTML_HEAD}
    <body>
        <nav class="navbar navbar-expand-lg">
            <div class="container">
                <a class="navbar-brand" href="/"><i class="fas fa-home"></i> Vajra Properties</a>
                <div class="d-flex">
                    <a class="nav-link" href="/">Home</a>
                    <a class="nav-link" href="/add-property">Sell Your Property</a>
                    <a class="nav-link" href="/admin">Admin Login</a>
                </div>
            </div>
        </nav>

        <div class="hero">
            <div class="container">
                <h1>Find Your Dream Home</h1>
                <p class="lead">Premium Real Estate in Virar, Vasai & Mumbai</p>
                
                <div class="search-box text-dark text-start">
                    <form action="/" method="get" class="row g-3">
                        <div class="col-md-4">
                            <label class="form-label fw-bold">I want to</label>
                            <select name="category" class="form-select">
                                <option value="All">Show All</option>
                                <option value="Buy">Buy a Home</option>
                                <option value="Rent">Rent a Home</option>
                            </select>
                        </div>
                        <div class="col-md-5">
                            <label class="form-label fw-bold">Location</label>
                            <input type="text" name="location" class="form-control" placeholder="e.g. Virar West">
                        </div>
                        <div class="col-md-3 d-flex align-items-end">
                            <button type="submit" class="btn btn-primary w-100"><i class="fas fa-search"></i> Search</button>
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
            <p>© 2026 Vajra Properties. All Rights Reserved.</p>
        </footer>

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
                <a class="navbar-brand" href="/">⬅ Back to Home</a>
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
                                <input name="title" class="form-control" required placeholder="e.g. 2BHK Flat near Station">
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
                                    <input name="price" class="form-control" required placeholder="e.g. 50 Lakhs">
                                </div>
                            </div>

                            <div class="mb-3">
                                <label>Location</label>
                                <input name="location" class="form-control" required placeholder="e.g. Virar West, Global City">
                            </div>

                            <div class="mb-3">
                                <label>Description</label>
                                <textarea name="description" class="form-control" rows="3"></textarea>
                            </div>

                            <div class="mb-3">
                                <label>Image URL</label>
                                <input name="image" class="form-control" placeholder="https://...">
                                <small class="text-muted">Paste a link to an image (right click image > copy image address)</small>
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
    title: str = Form(...), 
    location: str = Form(...),
    price: str = Form(...), 
    description: str = Form(...),
    image: str = Form(...),
    category: str = Form(...),
    db: Session = Depends(get_db)
):
    new_property = models.Property(
        title=title,
        location=location,
        price=price,
        description=description,
        image=image,
        category=category 
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