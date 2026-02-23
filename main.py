from fastapi import FastAPI, Form, Depends, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database import engine, SessionLocal
import models
from models import Property 
from auth import router as auth_router
from typing import Optional, List
import shutil
import os
import json
import urllib.parse
import re
import cloudinary
import cloudinary.uploader

# ---------------------------------------------------------
# 1. CLOUDINARY SETUP 
# ---------------------------------------------------------
cloudinary.config( 
  cloud_name = "dmqqvdspe", 
  api_key = "581944738912421", 
  api_secret = "w_lE8Dc6xPoUKrzF_5JrPaPHJhY",
  secure = True
)

# --- DATABASE SETUP ---
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

os.makedirs("static/images", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(auth_router)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- HELPER FUNCTIONS ---
def parse_images(image_data):
    if not image_data: return ["https://via.placeholder.com/600?text=No+Image"]
    try: return json.loads(image_data)
    except: return [image_data]

def optimize_url(url, width=500):
    if "cloudinary.com" not in url: return url 
    parts = url.split("/upload/")
    if len(parts) == 2:
        return f"{parts[0]}/upload/w_{width},c_fill,q_auto,f_auto/{parts[1]}"
    return url

def get_youtube_embed(url):
    if not url: return None
    regex = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})"
    match = re.search(regex, url)
    if match: return f"https://www.youtube.com/embed/{match.group(1)}"
    return None

# --- CSS & STYLING ---
HTML_HEAD = """
<head>
    <title>Vajrai Properties | Modern Living</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🏢</text></svg>">
    
    <meta name="description" content="Find your dream home in Virar, Vasai, and Mumbai. Premium flats, commercial spaces, and trusted real estate services.">
    <meta property="og:title" content="Vajrai Properties | Virar-Vasai Real Estate">
    <meta property="og:description" content="100+ Happy Clients. Buy, sell, or rent your property with the most trusted agents in the region. Click to view our latest listings.">
    <meta property="og:image" content="https://images.unsplash.com/photo-1600596542815-2495db9b639e?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80">
    <meta property="og:type" content="website">
    <meta name="twitter:card" content="summary_large_image">

    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

    <style>
        body { font-family: 'Poppins', sans-serif; background-color: #f8f9fa; margin: 0; padding: 0; }
        .navbar { background: white; box-shadow: 0 4px 15px rgba(0,0,0,0.05); padding: 12px 0; }
        .navbar-brand { font-weight: 700; color: #0f172a; font-size: 1.4rem; letter-spacing: -0.5px; }
        .nav-link { color: #475569; font-weight: 500; margin-left: 20px; transition: 0.3s; }
        .nav-link:hover, .nav-link.active { color: #0d6efd; }
        .hero {
            background: linear-gradient(to bottom, rgba(15, 23, 42, 0.6), rgba(15, 23, 42, 0.85)), url('https://images.unsplash.com/photo-1600596542815-2495db9b639e?ixlib=rb-4.0.3&auto=format&fit=crop&w=1600&q=80');
            background-size: cover; background-position: center; height: 25vh; min-height: 280px;
            display: flex; align-items: center; justify-content: center; text-align: center; color: white; padding-bottom: 30px; 
        }
        .hero h1 { font-size: 2.2rem; font-weight: 700; margin-bottom: 5px; text-shadow: 0 2px 4px rgba(0,0,0,0.3); }
        .hero p.lead { font-size: 1rem; color: #cbd5e1; margin-bottom: 15px !important; }
        .option-card {
            background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 12px; padding: 10px; margin: 0 5px;
            color: white; transition: all 0.3s ease; cursor: pointer; min-height: 90px; display: flex; flex-direction: column; justify-content: center;
        }
        .option-card:hover { background: rgba(255, 255, 255, 0.2); transform: translateY(-3px); }
        .option-icon { font-size: 1.6rem; margin-bottom: 5px; color: #38bdf8; }
        .search-container { margin-top: -35px; position: relative; z-index: 10; }
        .search-card { background: white; border-radius: 12px; border: none; box-shadow: 0 10px 30px rgba(0,0,0,0.12); padding: 8px; }
        .bg-light-alt { background-color: #f1f5f9; border-top: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0; }
        .btn-service { background: white; color: #475569; padding: 12px 24px; border-radius: 50px; text-decoration: none; font-weight: 500; font-size: 0.95rem; border: 1px solid #cbd5e1; transition: all 0.3s ease; display: flex; align-items: center; gap: 8px; }
        .btn-service:hover { background: #0f172a; color: white; border-color: #0f172a; transform: translateY(-3px); box-shadow: 0 10px 20px rgba(15, 23, 42, 0.15); }
        .feature-box { padding: 20px; text-align: center; transition: 0.3s; border-radius: 12px; }
        .feature-box:hover { background: white; box-shadow: 0 10px 30px rgba(0,0,0,0.05); transform: translateY(-5px); }
        .feature-box i { font-size: 2.5rem; color: #0d6efd; margin-bottom: 15px; }
        .property-card { border: none; border-radius: 16px; overflow: hidden; background: white; box-shadow: 0 4px 15px rgba(0,0,0,0.04); transition: 0.3s; border: 1px solid #f1f5f9; }
        .property-card:hover { transform: translateY(-8px); box-shadow: 0 15px 30px rgba(0,0,0,0.1); }
        .card-img-top { height: 220px; object-fit: cover; }
        .badge-category { position: absolute; top: 15px; left: 15px; padding: 6px 16px; border-radius: 30px; color: white; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; z-index: 10; }
        .bg-rent { background-color: #0ea5e9; }
        .bg-buy { background-color: #8b5cf6; }
        .sold-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(255, 255, 255, 0.7); display: flex; align-items: center; justify-content: center; z-index: 5; }
        .sold-badge { background: #dc3545; color: white; font-weight: 800; padding: 10px 30px; font-size: 1.5rem; transform: rotate(-15deg); border: 4px solid white; box-shadow: 0 5px 15px rgba(0,0,0,0.3); text-transform: uppercase; }
        .sticky-sidebar { position: sticky; top: 100px; z-index: 10; }
        .mobile-bottom-nav { position: fixed; bottom: 0; left: 0; width: 100%; background: white; box-shadow: 0 -5px 15px rgba(0,0,0,0.1); padding: 12px 15px; display: flex; justify-content: space-between; z-index: 1000; }
        .mobile-bottom-nav .btn { flex: 1; margin: 0 5px; border-radius: 8px; }
        .admin-stat-card { background: white; padding: 25px; border-radius: 12px; border: 1px solid #e2e8f0; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.02); }
        .admin-stat-card h2 { font-weight: 800; margin: 0; color: #0f172a; font-size: 2.5rem; }
        .table-custom { background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.02); margin-top: 20px; }
        .table-custom th { background-color: #f8fafc; color: #475569; font-weight: 600; text-transform: uppercase; font-size: 0.85rem; padding: 15px; border-bottom: 2px solid #e2e8f0; }
        .table-custom td { padding: 15px; vertical-align: middle; border-bottom: 1px solid #f1f5f9; color: #334155; }
        .whatsapp-float { position: fixed; width: 60px; height: 60px; bottom: 30px; right: 30px; background-color: #25d366; color: #FFF; border-radius: 50px; text-align: center; font-size: 30px; z-index: 900; display: flex; align-items: center; justify-content: center; text-decoration: none; box-shadow: 0 4px 15px rgba(37, 211, 102, 0.4); transition: 0.3s; }
        .whatsapp-float:hover { transform: scale(1.1); }
        .map-container, .video-container { overflow: hidden; padding-bottom: 56.25%; position: relative; height: 0; border-radius: 10px; margin-top: 20px; background: #eee; }
        .map-container iframe, .video-container iframe { left: 0; top: 0; height: 100%; width: 100%; position: absolute; border: none; }
    </style>
</head>
"""

# ---------------- HOME PAGE ----------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db), category: Optional[str] = None, location: Optional[str] = None):
    is_admin = request.cookies.get("admin_token") == "logged_in"
    query = db.query(Property)
    if category and category != "All":
        query = query.filter(Property.category == category)
    if location:
        query = query.filter(Property.location.contains(location))
    properties = query.all()

    cards_html = ""
    for p in properties:
        badge_color = "bg-buy" if p.category == "Buy" else "bg-rent"
        thumbnail = optimize_url(parse_images(p.image)[0], width=400)
        sold_overlay = ""
        if p.status == "Sold": sold_overlay = '<div class="sold-overlay"><div class="sold-badge">SOLD</div></div>'
        elif p.status == "Rented": sold_overlay = '<div class="sold-overlay"><div class="sold-badge bg-primary">RENTED</div></div>'
        cards_html += f"""
        <div class="col-12 col-md-6 col-lg-4 col-xl-3 mb-4">
            <div class="property-card h-100 d-flex flex-column">
                <div style="position:relative">
                    <span class="badge-category {badge_color}">{p.category}</span>
                    {sold_overlay}
                    <a href="/property/{p.id}">
                        <img src="{thumbnail}" class="card-img-top" alt="Property Image" loading="lazy">
                    </a>
                </div>
                <div class="card-body d-flex flex-column">
                    <h5 class="card-title text-truncate fw-bold mb-2" style="font-size:1.15rem; color:#0f172a;">{p.title}</h5>
                    <p class="text-muted small mb-3"><i class="fas fa-map-marker-alt text-danger me-1"></i> {p.location}</p>
                    <h4 class="text-primary fw-bold mb-3 mt-auto">₹ {p.price}</h4>
                    <a href="/property/{p.id}" class="btn btn-primary w-100 fw-bold">View Details</a>
                </div>
            </div>
        </div>
        """

    nav_links = """
    <a class="nav-link fw-bold text-primary" href="/dashboard"><i class="fas fa-chart-line me-1"></i> Dashboard</a>
    <a class="nav-link text-danger" href="/logout"><i class="fas fa-sign-out-alt me-1"></i> Logout</a>
    """ if is_admin else '<a class="nav-link" href="/login"><i class="fas fa-user-lock me-1"></i> Admin</a>'

    return f"""
    <!DOCTYPE html>
    <html>
    {HTML_HEAD}
    <body>
        <nav class="navbar navbar-expand-lg sticky-top">
            <div class="container">
                <a class="navbar-brand" href="/"><i class="fas fa-building text-primary me-2"></i>Vajrai Properties</a>
                <div class="d-flex align-items-center">
                    <a class="nav-link d-none d-md-block" href="mailto:pankaj@vajraiproperties.com"><i class="fas fa-envelope"></i> pankaj@vajraiproperties.com</a>
                    <a class="nav-link active" href="/">Home</a>
                    {nav_links}
                </div>
            </div>
        </nav>

        <div class="hero">
            <div class="container">
                <h1>Find Your Dream Home</h1>
                <p class="lead mb-4">Premium Flats & Commercial Spaces in Virar-Vasai</p>
                <div class="row justify-content-center mt-2">
                    <div class="col-4 col-md-3"><a href="/?category=Buy" style="text-decoration:none;"><div class="option-card"><i class="fas fa-home option-icon"></i><h3 class="h5 fw-bold m-0">BUY</h3></div></a></div>
                    <div class="col-4 col-md-3"><a href="https://wa.me/918999338010?text=I%20want%20to%20sell%20my%20property" target="_blank" style="text-decoration:none;"><div class="option-card"><i class="fas fa-tags option-icon"></i><h3 class="h5 fw-bold m-0">SELL</h3></div></a></div>
                    <div class="col-4 col-md-3"><a href="/?category=Rent" style="text-decoration:none;"><div class="option-card"><i class="fas fa-key option-icon"></i><h3 class="h5 fw-bold m-0">RENT</h3></div></a></div>
                </div>
            </div>
        </div>

        <div class="container search-container">
            <div class="card search-card mx-auto" style="max-width:850px;">
                <form action="/" method="get" class="row g-2 align-items-center p-2">
                    <div class="col-md-3">
                        <select name="category" class="form-select form-select-lg border-0 bg-light text-secondary fw-bold">
                            <option value="All">All Types</option>
                            <option value="Buy">Buy</option>
                            <option value="Rent">Rent</option>
                        </select>
                    </div>
                    <div class="col-md-6 border-start border-end d-none d-md-block">
                        <input type="text" name="location" class="form-control form-control-lg border-0 shadow-none" placeholder="Search Location (e.g. Virar West)...">
                    </div>
                    <div class="col-md-6 d-md-none mt-2 mb-2">
                        <input type="text" name="location" class="form-control form-control-lg bg-light border-0" placeholder="Search Location...">
                    </div>
                    <div class="col-md-3">
                        <button type="submit" class="btn btn-primary btn-lg w-100 fw-bold"><i class="fas fa-search me-2"></i>Search</button>
                    </div>
                </form>
            </div>
        </div>

        <div class="bg-light-alt mt-5">
            <div class="container text-center py-4">
                <h3 class="fw-bold mb-4" style="color:#0f172a;">Financial & Legal Services</h3>
                <div class="d-flex justify-content-center gap-3 flex-wrap">
                    <a href="https://wa.me/918999338010?text=I want to know about Home Loans" class="btn-service" target="_blank"><i class="fas fa-building-columns"></i> Home Loan</a>
                    <a href="https://wa.me/918999338010?text=I want to know about Mortgage Loans" class="btn-service" target="_blank"><i class="fas fa-file-invoice-dollar"></i> Mortgage Loan</a>
                    <a href="https://wa.me/918999338010?text=I need help with Property Registration" class="btn-service" target="_blank"><i class="fas fa-stamp"></i> Property Registration</a>
                    <a href="https://wa.me/918999338010?text=I need help making a Rent Agreement" class="btn-service" target="_blank"><i class="fas fa-file-signature"></i> Rent Agreement</a>
                </div>
            </div>
        </div>

        <div class="container-fluid px-4 px-xl-5 mt-5 pt-3">
            <div class="d-flex justify-content-between align-items-end mb-4">
                <h3 style="font-weight:700; color:#0f172a; margin:0;">Latest Properties</h3>
                <a href="/" class="text-primary text-decoration-none fw-bold">View All <i class="fas fa-arrow-right ms-1"></i></a>
            </div>
            <div class="row">{cards_html if cards_html else '<div class="col-12 text-center text-muted my-5 py-5"><i class="fas fa-home fa-3x mb-3 text-light"></i><br>No properties listed yet.</div>'}</div>
        </div>

        <div class="container my-5 pt-5 border-top">
            <div class="row text-center">
                <div class="col-md-4 mb-4"><div class="feature-box"><i class="fas fa-handshake"></i><h5>Trusted Agent</h5><p class="text-muted small">100+ Happy Clients placed in their dream homes.</p></div></div>
                <div class="col-md-4 mb-4"><div class="feature-box"><i class="fas fa-tags"></i><h5>Best Deals</h5><p class="text-muted small">Directly negotiated from owner listings.</p></div></div>
                <div class="col-md-4 mb-4"><div class="feature-box"><i class="fas fa-map-marked-alt"></i><h5>Prime Locations</h5><p class="text-muted small">Properties strategically located near major stations.</p></div></div>
            </div>
        </div>

        <div class="container mt-5 mb-5">
            <div class="card shadow-sm p-4 mx-auto border-0" style="max-width: 800px; border-radius: 12px; background: #ffffff;">
                <h3 class="mb-4 text-center" style="font-weight: 600; color: #2c3e50;">Contact Us</h3>
                <form action="https://api.web3forms.com/submit" method="POST">
                    <input type="hidden" name="access_key" value="3d28f323-7f01-46d1-9acf-199f6bec2a04">
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label class="form-label">Your Name</label>
                            <input type="text" name="name" class="form-control bg-light" required placeholder="John Doe">
                        </div>
                        <div class="col-md-6 mb-3">
                            <label class="form-label">Phone Number</label>
                            <input type="tel" name="phone" class="form-control bg-light" required placeholder="+91 1234567890">
                        </div>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Email Address</label>
                        <input type="email" name="email" class="form-control bg-light" required placeholder="name@example.com">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Message</label>
                        <textarea name="message" class="form-control bg-light" rows="4" required placeholder="Hi, I am looking for a property in Virar West..."></textarea>
                    </div>
                    <input type="checkbox" name="botcheck" class="hidden" style="display: none;">
                    <button type="submit" class="btn btn-primary w-100 btn-lg">Send Message <i class="fas fa-paper-plane"></i></button>
                </form>
            </div>
        </div>

        <footer class="text-center pt-5 pb-4 text-muted">
            <p class="mb-2">
                <i class="fas fa-envelope"></i> <a href="mailto:pankaj@vajraiproperties.com" style="color: inherit; text-decoration: none;">pankaj@vajraiproperties.com</a>  |  
                <i class="fas fa-phone"></i> +91 8999338010
            </p>
            <p>© 2026 Vajrai Properties. All Rights Reserved.</p>
        </footer>
        <a href="https://wa.me/918999338010" class="whatsapp-float d-none d-md-flex" target="_blank"><i class="fab fa-whatsapp"></i></a>
    </body>
    </html>
    """

# ---------------- ADMIN DASHBOARD ----------------
@app.get("/dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    if request.cookies.get("admin_token") != "logged_in": return RedirectResponse(url="/login", status_code=303)
    properties = db.query(Property).all()
    total = len(properties)
    available = sum(1 for p in properties if p.status == "Available")
    sold = sum(1 for p in properties if p.status == "Sold")
    table_rows = ""
    for p in properties:
        thumb = optimize_url(parse_images(p.image)[0], width=100)
        badge = "bg-success" if p.status == "Available" else ("bg-danger" if p.status == "Sold" else "bg-primary")
        table_rows += f"""
        <tr>
            <td><img src="{thumb}" style="width: 70px; height: 50px; border-radius: 6px; object-fit: cover;"></td>
            <td class="fw-bold">{p.title}</td>
            <td class="text-muted small"><i class="fas fa-map-marker-alt"></i> {p.location}</td>
            <td class="fw-bold text-primary">₹ {p.price}</td>
            <td><span class="badge {badge}">{p.status}</span></td>
            <td>
                <a href="/property/{p.id}" class="btn btn-sm btn-outline-info" target="_blank"><i class="fas fa-eye"></i></a>
                <a href="/edit-property/{p.id}" class="btn btn-sm btn-outline-warning"><i class="fas fa-edit"></i></a>
                <a href="/delete-property/{p.id}" class="btn btn-sm btn-outline-danger" onclick="return confirm('Delete this property?')"><i class="fas fa-trash"></i></a>
            </td>
        </tr>
        """
    return f"""
    <!DOCTYPE html><html>{HTML_HEAD}<body class="bg-light">
    <nav class="navbar navbar-expand-lg sticky-top"><div class="container"><a class="navbar-brand" href="/"><i class="fas fa-building text-primary me-2"></i>Vajrai Admin</a>
    <div class="d-flex"><a class="nav-link fw-bold text-primary me-3" href="/add-property"><i class="fas fa-plus-circle me-1"></i> Add</a><a class="nav-link text-danger" href="/logout"><i class="fas fa-sign-out-alt"></i></a></div></div></nav>
    <div class="container mt-5">
        <h2 class="fw-bold mb-4">Dashboard</h2>
        <div class="row mb-4">
            <div class="col-md-4 mb-3"><div class="admin-stat-card"><h5 class="text-muted">Total Properties</h5><h2 class="text-primary">{total}</h2></div></div>
            <div class="col-md-4 mb-3"><div class="admin-stat-card"><h5 class="text-muted">Available</h5><h2 class="text-success">{available}</h2></div></div>
            <div class="col-md-4 mb-3"><div class="admin-stat-card"><h5 class="text-muted">Sold</h5><h2 class="text-danger">{sold}</h2></div></div>
        </div>
        <div class="card border-0 shadow-sm p-3 table-responsive">
            <table class="table table-custom table-hover align-middle mb-0">
                <thead><tr><th>Image</th><th>Property Title</th><th>Location</th><th>Price</th><th>Status</th><th>Actions</th></tr></thead>
                <tbody>{table_rows if table_rows else "<tr><td colspan='6' class='text-center py-4'>No properties found.</td></tr>"}</tbody>
            </table>
        </div>
    </div>
    </body></html>
    """

# ---------------- PROPERTY DETAILS ----------------
@app.get("/property/{pid}", response_class=HTMLResponse)
def property_details(pid: int, db: Session = Depends(get_db)):
    p = db.query(Property).filter(Property.id == pid).first()
    if not p: return HTMLResponse("<h1>Property Not Found</h1>", status_code=404)
    images = parse_images(p.image)
    carousel_items = ""
    for index, img_url in enumerate(images):
        active_class = "active" if index == 0 else ""
        optimized_img = optimize_url(img_url, width=800)
        carousel_items += f'<div class="carousel-item {active_class}"><img src="{optimized_img}" class="d-block w-100 rounded" style="height: 450px; object-fit: cover;" alt="Property Image"></div>'

    map_query = urllib.parse.quote(p.location)
    google_map_embed = f'<div class="map-container"><iframe src="https://maps.google.com/maps?q={map_query}&t=&z=14&ie=UTF8&iwloc=&output=embed" frameborder="0" scrolling="no" marginheight="0" marginwidth="0"></iframe></div>'
    
    video_embed = ""
    if p.video_url:
        embed_link = get_youtube_embed(p.video_url)
        if embed_link: video_embed = f'<div class="video-container"><iframe src="{embed_link}" allowfullscreen></iframe></div>'

    status_badge = '<span class="badge bg-danger ms-2">SOLD OUT</span>' if p.status == "Sold" else ('<span class="badge bg-primary ms-2">RENTED</span>' if p.status == "Rented" else '<span class="badge bg-success ms-2">AVAILABLE</span>')

    return f"""
    <!DOCTYPE html><html>{HTML_HEAD}<body>
        <nav class="navbar navbar-expand-lg"><div class="container"><a class="navbar-brand" href="/"><i class="fas fa-building text-primary me-2"></i>Vajrai Properties</a><a href="/" class="btn btn-outline-secondary btn-sm rounded-pill px-3"><i class="fas fa-arrow-left me-1"></i> Back</a></div></nav>
        <div class="container mt-4 mb-5 pb-5">
            <div class="row">
                <div class="col-lg-8 mb-4">
                    <div id="propCarousel" class="carousel slide mb-4 shadow-sm rounded" data-bs-ride="carousel">
                        <div class="carousel-inner">{carousel_items}</div>
                        <button class="carousel-control-prev" type="button" data-bs-target="#propCarousel" data-bs-slide="prev"><span class="carousel-control-prev-icon bg-dark rounded-circle p-3"></span></button>
                        <button class="carousel-control-next" type="button" data-bs-target="#propCarousel" data-bs-slide="next"><span class="carousel-control-next-icon bg-dark rounded-circle p-3"></span></button>
                    </div>
                    <div class="bg-white p-4 rounded shadow-sm border border-light">
                        <ul class="nav nav-tabs mb-3" id="myTab" role="tablist">
                            <li class="nav-item"><button class="nav-link active fw-bold" data-bs-toggle="tab" data-bs-target="#details"><i class="fas fa-info-circle me-1"></i> Description</button></li>
                            <li class="nav-item"><button class="nav-link fw-bold" data-bs-toggle="tab" data-bs-target="#map"><i class="fas fa-map me-1"></i> Location Map</button></li>
                            { '<li class="nav-item"><button class="nav-link fw-bold" data-bs-toggle="tab" data-bs-target="#video"><i class="fas fa-video me-1"></i> Video Tour</button></li>' if video_embed else '' }
                        </ul>
                        <div class="tab-content" id="myTabContent">
                            <div class="tab-pane fade show active" id="details"><p style="white-space: pre-line; color:#475569; font-size: 1.05rem; line-height: 1.8;">{p.description}</p></div>
                            <div class="tab-pane fade" id="map">{google_map_embed}</div>
                            <div class="tab-pane fade" id="video">{video_embed}</div>
                        </div>
                    </div>
                </div>
                <div class="col-lg-4">
                    <div class="sticky-sidebar">
                        <div class="card shadow-sm p-4 border-0 mb-4 bg-white">
                            <div class="d-flex justify-content-between align-items-center mb-3">
                                <span class="badge bg-dark px-3 py-2">{p.category}</span> {status_badge}
                            </div>
                            <h2 class="fw-bold text-dark">{p.title}</h2>
                            <p class="text-muted"><i class="fas fa-map-marker-alt text-danger"></i> {p.location}</p>
                            <h2 class="text-primary fw-bold mb-4">₹ {p.price}</h2>
                            <div class="d-none d-md-block">
                                <a href="https://wa.me/918999338010?text=Hi, I am interested in {p.title}" class="btn btn-success w-100 mb-3 btn-lg fw-bold"><i class="fab fa-whatsapp me-2"></i> WhatsApp Agent</a>
                                <a href="tel:+918999338010" class="btn btn-outline-dark w-100 fw-bold"><i class="fas fa-phone-alt me-2"></i> Call Now</a>
                                <a href="mailto:pankaj@vajraiproperties.com?subject=Inquiry about {p.title}" class="btn btn-outline-primary w-100 mt-2"><i class="fas fa-envelope"></i> Email Agent</a>
                            </div>
                        </div>
                        <div class="card shadow-sm p-4 border-0 bg-white">
                            <h5 class="text-center mb-3 fw-bold text-dark"><i class="fas fa-calculator text-primary"></i> EMI Calculator</h5>
                            <label class="small text-muted fw-bold">Loan Amount (₹)</label>
                            <input type="number" id="loanAmt" class="form-control mb-3 bg-light" placeholder="e.g. 5000000">
                            <div class="row">
                                <div class="col-6">
                                    <label class="small text-muted fw-bold">Interest (%)</label>
                                    <input type="number" id="intRate" class="form-control mb-3 bg-light" value="8.5" step="0.1">
                                </div>
                                <div class="col-6">
                                    <label class="small text-muted fw-bold">Years</label>
                                    <input type="number" id="years" class="form-control mb-4 bg-light" value="20">
                                </div>
                            </div>
                            <button onclick="calcEMI()" class="btn btn-primary w-100 fw-bold">Calculate</button>
                            <div id="emiResult" class="calc-result text-success fw-bold text-center mt-3" style="font-size: 1.4rem;"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="mobile-bottom-nav d-lg-none">
            <a href="tel:+918999338010" class="btn btn-dark fw-bold py-2"><i class="fas fa-phone-alt me-1"></i> Call Agent</a>
            <a href="https://wa.me/918999338010?text=Interested in {p.title}" class="btn btn-success fw-bold py-2"><i class="fab fa-whatsapp me-1"></i> WhatsApp</a>
        </div>
        <script>
            function calcEMI() {{
                let p = document.getElementById('loanAmt').value;
                let r = document.getElementById('intRate').value / 12 / 100;
                let n = document.getElementById('years').value * 12;
                if(p && r && n) {{
                    let emi = p * r * (Math.pow(1+r,n) / (Math.pow(1+r,n)-1));
                    document.getElementById('emiResult').innerText = "₹ " + Math.round(emi).toLocaleString() + " /mo";
                }}
            }}
        </script>
    </body></html>
    """

# ---------------- ADD & EDIT FORMS ----------------
@app.get("/add-property", response_class=HTMLResponse)
def add_property_form(request: Request):
    if request.cookies.get("admin_token") != "logged_in": return RedirectResponse(url="/login", status_code=303)
    return f"""
    <!DOCTYPE html><html>{HTML_HEAD}<body class="bg-light">
    <nav class="navbar"><div class="container"><a class="navbar-brand" href="/dashboard"><i class="fas fa-arrow-left me-2"></i> Back to Dashboard</a></div></nav>
    <div class="container mt-5 mb-5"><div class="card shadow-sm p-4 mx-auto border-0" style="max-width: 650px; border-radius:12px;">
    <h3 class="mb-4 fw-bold text-dark"><i class="fas fa-plus-circle text-primary me-2"></i>Add New Property</h3>
    <form action="/add-property" method="post" enctype="multipart/form-data">
    <label class="form-label fw-bold text-muted small">Property Title</label><input name="title" class="form-control mb-3 bg-light" required>
    <div class="row mb-3"><div class="col"><label class="form-label fw-bold text-muted small">Category</label><select name="category" class="form-select bg-light"><option value="Buy">Sell</option><option value="Rent">Rent</option></select></div>
    <div class="col"><label class="form-label fw-bold text-muted small">Price (e.g. 45 Lakh)</label><input name="price" class="form-control bg-light" required></div></div>
    <label class="form-label fw-bold text-muted small">Location (e.g. Virar West)</label><input name="location" class="form-control mb-3 bg-light" required>
    <label class="form-label fw-bold text-muted small">YouTube Video Link (Optional)</label><input name="video_url" class="form-control mb-3 bg-light" placeholder="https://youtu.be/...">
    <label class="form-label fw-bold text-muted small">Full Description</label><textarea name="description" class="form-control mb-4 bg-light" rows="5"></textarea>
    <label class="fw-bold form-label text-primary"><i class="fas fa-images me-1"></i> Upload Photos (Max 5)</label>
    <input type="file" id="photoInput" name="image_files" class="form-control mb-2" accept="image/*" multiple required>
    <ul id="filePreview" class="small mb-4 px-3" style="list-style-type: none; padding-left: 0;"></ul>
    <button type="submit" class="btn btn-primary w-100 py-2 fw-bold fs-5">Publish Property</button>
    </form></div></div>
    <script>
        const dt = new DataTransfer(); 
        const input = document.getElementById('photoInput');
        const preview = document.getElementById('filePreview');
        input.addEventListener('change', function(e) {{
            for(let i = 0; i < this.files.length; i++) {{
                if(dt.items.length < 5) {{
                    dt.items.add(this.files[i]);
                }} else {{
                    alert("Maximum limit reached. You can only upload up to 5 photos.");
                    break;
                }}
            }}
            this.files = dt.files;
            preview.innerHTML = "";
            for(let i = 0; i < this.files.length; i++) {{
                preview.innerHTML += "<li class='text-success mb-1'><i class='fas fa-check-circle me-2'></i>" + this.files[i].name + "</li>";
            }}
        }});
    </script>
    </body></html>
    """

@app.post("/add-property")
async def save_property(request: Request, title: str = Form(...), location: str = Form(...), price: str = Form(...), description: str = Form(...), category: str = Form(...), video_url: Optional[str] = Form(None), image_files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    if request.cookies.get("admin_token") != "logged_in": return RedirectResponse(url="/login", status_code=303)
    uploaded_urls = []
    for file in image_files:
        try:
            res = cloudinary.uploader.upload(file.file)
            uploaded_urls.append(res.get("url"))
        except: pass
    new_prop = Property(title=title, location=location, price=price, description=description, image=json.dumps(uploaded_urls), category=category, status="Available", video_url=video_url)
    db.add(new_prop)
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=303)

@app.post("/edit-property/{pid}")
def update_property(pid: int, request: Request, title: str = Form(...), price: str = Form(...), location: str = Form(...), description: str = Form(...), status: str = Form(...), video_url: Optional[str] = Form(None), db: Session = Depends(get_db)):
    if request.cookies.get("admin_token") != "logged_in": return RedirectResponse(url="/login", status_code=303)
    p = db.query(Property).filter(Property.id == pid).first()
    if p:
        p.title = title
        p.price = price
        p.location = location
        p.description = description
        p.status = status 
        p.video_url = video_url
        db.commit()
    return RedirectResponse(url=f"/property/{pid}", status_code=303)

@app.get("/delete-property/{pid}")
def delete_property(pid: int, request: Request, db: Session = Depends(get_db)):
    if request.cookies.get("admin_token") != "logged_in": return RedirectResponse(url="/login", status_code=303)
    prop = db.query(Property).filter(Property.id == pid).first()
    if prop: db.delete(prop); db.commit()
    return RedirectResponse(url="/dashboard", status_code=303)

# ---------------- RESET DB ----------------
@app.get("/reset-db", response_class=HTMLResponse)
def reset_database():
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    return "<h1 style='color:green; text-align:center; margin-top:50px;'>Database Reset Successful!<br><a href='/'>Go Home</a></h1>"

# ---------------- SITEMAP GENERATOR ----------------
@app.get("/sitemap.xml")
def get_sitemap(db: Session = Depends(get_db)):
    # Define your static pages
    pages = ["", "login"]
    
    # Get all property IDs to create dynamic links
    properties = db.query(Property).all()
    for p in properties:
        pages.append(f"property/{p.id}")

    # Build the XML structure
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    for page in pages:
        sitemap_xml += f'<url><loc>https://vajraiproperties.com/{page}</loc><changefreq>daily</changefreq></url>'
    sitemap_xml += '</urlset>'

    return HTMLResponse(content=sitemap_xml, media_type="application/xml")

@app.get("/robots.txt", response_class=HTMLResponse)
def robots_txt():
    content = "User-agent: *\nAllow: /\n\nSitemap: https://vajraiproperties.com/sitemap.xml"
    return HTMLResponse(content=content, media_type="text/plain")