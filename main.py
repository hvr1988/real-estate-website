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

# Setup Image Storage
os.makedirs("static/images", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_router)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- HELPER: IMAGES ---
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

# --- HELPER: EXTRACT YOUTUBE ID ---
def get_youtube_embed(url):
    if not url: return None
    regex = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})"
    match = re.search(regex, url)
    if match:
        return f"https://www.youtube.com/embed/{match.group(1)}"
    return None

# --- CSS & STYLING ---
HTML_HEAD = """
<head>
    <title>Vajrai Properties | Modern Living</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

    <style>
        body { font-family: 'Poppins', sans-serif; background-color: #f8f9fa; margin: 0; padding: 0; }
        
        /* Navbar */
        .navbar { background: white; box-shadow: 0 4px 15px rgba(0,0,0,0.05); padding: 12px 0; }
        .navbar-brand { font-weight: 700; color: #0f172a; font-size: 1.4rem; letter-spacing: -0.5px; }
        .nav-link { color: #475569; font-weight: 500; margin-left: 20px; transition: 0.3s; }
        .nav-link:hover { color: #0d6efd; }
        
        /* Hero Section */
        .hero {
            background: linear-gradient(to bottom, rgba(15, 23, 42, 0.6), rgba(15, 23, 42, 0.85)), url('https://images.unsplash.com/photo-1600596542815-2495db9b639e?ixlib=rb-4.0.3&auto=format&fit=crop&w=1600&q=80');
            background-size: cover; background-position: center; 
            height: 25vh; min-height: 280px;
            display: flex; align-items: center; justify-content: center; text-align: center; color: white;
            padding-bottom: 30px; 
        }
        .hero h1 { font-size: 2.2rem; font-weight: 700; margin-bottom: 5px; text-shadow: 0 2px 4px rgba(0,0,0,0.3); }
        .hero p.lead { font-size: 1rem; color: #cbd5e1; margin-bottom: 15px !important; }
        
        /* Option Cards */
        .option-card {
            background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 12px; padding: 10px; margin: 0 5px;
            color: white; transition: all 0.3s ease; cursor: pointer; 
            min-height: 90px; display: flex; flex-direction: column; justify-content: center;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        .option-card:hover { background: rgba(255, 255, 255, 0.2); transform: translateY(-3px); border-color: rgba(255,255,255,0.4); }
        .option-icon { font-size: 1.6rem; margin-bottom: 5px; color: #38bdf8; }
        
        /* Search Bar */
        .search-container { margin-top: -35px; position: relative; z-index: 10; }
        .search-card { background: white; border-radius: 12px; border: none; box-shadow: 0 10px 30px rgba(0,0,0,0.12); padding: 8px; }
        
        /* Alternating Background Section */
        .bg-light-alt { background-color: #f1f5f9; border-top: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0; }
        
        /* Services Buttons */
        .services-container { text-align: center; padding: 40px 20px; max-width: 1000px; margin: 0 auto; }
        .services-container h3 { color: #0f172a; margin-bottom: 25px; font-size: 1.5rem; font-weight: 700; }
        .service-buttons { display: flex; justify-content: center; gap: 15px; flex-wrap: wrap; }
        .btn-service { 
            background: white; color: #475569; padding: 12px 24px; border-radius: 50px; 
            text-decoration: none; font-weight: 500; font-size: 0.95rem; border: 1px solid #cbd5e1; 
            transition: all 0.3s ease; box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            display: flex; align-items: center; gap: 8px;
        }
        .btn-service i { font-size: 1.1rem; color: #0d6efd; }
        .btn-service:hover { background: #0f172a; color: white; border-color: #0f172a; transform: translateY(-3px); box-shadow: 0 10px 20px rgba(15, 23, 42, 0.15); }
        .btn-service:hover i { color: #38bdf8; }

        /* Property Cards */
        .property-card { border: none; border-radius: 16px; overflow: hidden; background: white; box-shadow: 0 4px 15px rgba(0,0,0,0.04); transition: 0.3s; border: 1px solid #f1f5f9; }
        .property-card:hover { transform: translateY(-8px); box-shadow: 0 15px 30px rgba(0,0,0,0.1); }
        .card-img-top { height: 220px; object-fit: cover; }
        .badge-category { position: absolute; top: 15px; left: 15px; padding: 6px 16px; border-radius: 30px; color: white; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; z-index: 10; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
        .bg-rent { background-color: #0ea5e9; }
        .bg-buy { background-color: #8b5cf6; }
        .sold-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(255, 255, 255, 0.7); display: flex; align-items: center; justify-content: center; z-index: 5; }
        .sold-badge { background: #dc3545; color: white; font-weight: 800; padding: 10px 30px; font-size: 1.5rem; transform: rotate(-15deg); border: 4px solid white; box-shadow: 0 5px 15px rgba(0,0,0,0.3); text-transform: uppercase; }
        
        /* Trust Features */
        .feature-box { padding: 20px; text-align: center; transition: 0.3s; border-radius: 12px; }
        .feature-box:hover { background: white; box-shadow: 0 10px 30px rgba(0,0,0,0.05); transform: translateY(-5px); }
        .feature-box i { font-size: 2.5rem; color: #0d6efd; margin-bottom: 15px; }
        .feature-box h5 { font-weight: 700; color: #0f172a; }

        /* Mega Footer */
        .mega-footer { background-color: #0f172a; color: #94a3b8; padding: 60px 0 20px 0; margin-top: 60px; }
        .mega-footer h5 { color: white; font-weight: 600; margin-bottom: 20px; }
        .mega-footer a { color: #94a3b8; text-decoration: none; transition: 0.3s; }
        .mega-footer a:hover { color: #38bdf8; padding-left: 5px; }
        .mega-footer ul li { margin-bottom: 10px; }
        .footer-bottom { border-top: 1px solid #1e293b; margin-top: 40px; padding-top: 20px; font-size: 0.85rem; }
        
        .whatsapp-float { position: fixed; width: 60px; height: 60px; bottom: 30px; right: 30px; background-color: #25d366; color: #FFF; border-radius: 50px; text-align: center; font-size: 30px; z-index: 100; display: flex; align-items: center; justify-content: center; text-decoration: none; box-shadow: 0 4px 15px rgba(37, 211, 102, 0.4); transition: 0.3s; }
        .whatsapp-float:hover { transform: scale(1.1); }
        
        /* Calculator Styles */
        .calc-box { background: #f8f9fa; padding: 20px; border-radius: 10px; border: 1px solid #ddd; margin-top: 20px; }
        .calc-result { font-size: 1.5rem; color: #28a745; font-weight: bold; text-align: center; margin-top: 10px; }
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
        
        admin_controls = ""
        if is_admin:
            admin_controls = f"""
            <div class="d-flex gap-2 mt-3 pt-3 border-top">
                <a href="/edit-property/{p.id}" class="btn btn-outline-secondary btn-sm w-50"><i class="fas fa-edit"></i> Edit</a>
                <a href="/delete-property/{p.id}" class="btn btn-outline-danger btn-sm w-50" onclick="return confirm('Delete this property?')"><i class="fas fa-trash"></i></a>
            </div>
            """

        images = parse_images(p.image)
        thumbnail = optimize_url(images[0], width=400)

        sold_overlay = ""
        if p.status == "Sold":
            sold_overlay = '<div class="sold-overlay"><div class="sold-badge">SOLD</div></div>'
        elif p.status == "Rented":
            sold_overlay = '<div class="sold-overlay"><div class="sold-badge bg-primary">RENTED</div></div>'

        cards_html += f"""
        <div class="col-md-4 mb-4">
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
                    {admin_controls}
                </div>
            </div>
        </div>
        """

    if is_admin:
        nav_links = """
        <a class="nav-link fw-bold text-primary" href="/add-property"><i class="fas fa-plus-circle me-1"></i> Add Property</a>
        <a class="nav-link text-danger" href="/logout"><i class="fas fa-sign-out-alt me-1"></i> Logout</a>
        """
    else:
        nav_links = '<a class="nav-link" href="/admin"><i class="fas fa-user-lock me-1"></i> Admin</a>'

    return f"""
    <!DOCTYPE html>
    <html>
    {HTML_HEAD}
    <body>
        <nav class="navbar navbar-expand-lg sticky-top">
            <div class="container">
                <a class="navbar-brand" href="/"><i class="fas fa-building text-primary me-2"></i>Vajrai Properties</a>
                <div class="d-flex align-items-center">
                    <a class="nav-link" href="/">Home</a>
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
            <div class="services-container">
                <h3>Financial & Legal Services</h3>
                <div class="service-buttons">
                    <a href="https://wa.me/918999338010?text=I want to know about Home Loans" class="btn-service" target="_blank">
                        <i class="fas fa-building-columns"></i> Home Loan
                    </a>
                    <a href="https://wa.me/918999338010?text=I want to know about Mortgage Loans" class="btn-service" target="_blank">
                        <i class="fas fa-file-invoice-dollar"></i> Mortgage Loan
                    </a>
                    <a href="https://wa.me/918999338010?text=I need help with Property Registration" class="btn-service" target="_blank">
                        <i class="fas fa-stamp"></i> Property Registration
                    </a>
                    <a href="https://wa.me/918999338010?text=I need help making a Rent Agreement" class="btn-service" target="_blank">
                        <i class="fas fa-file-signature"></i> Rent Agreement
                    </a>
                </div>
            </div>
        </div>

        <div class="container mt-5 pt-3">
            <div class="d-flex justify-content-between align-items-end mb-4">
                <h3 style="font-weight:700; color:#0f172a; margin:0;">Latest Properties</h3>
                <a href="/" class="text-primary text-decoration-none fw-bold">View All <i class="fas fa-arrow-right ms-1"></i></a>
            </div>
            <div class="row">
                {cards_html if cards_html else '<div class="col-12 text-center text-muted my-5 py-5"><i class="fas fa-home fa-3x mb-3 text-light"></i><br>No properties listed yet.</div>'}
            </div>
        </div>

        <div class="container my-5 pt-5 border-top">
            <div class="row text-center">
                <div class="col-md-4 mb-4">
                    <div class="feature-box">
                        <i class="fas fa-handshake"></i>
                        <h5>Trusted Agent</h5>
                        <p class="text-muted small">100+ Happy Clients placed in their dream homes across the region.</p>
                    </div>
                </div>
                <div class="col-md-4 mb-4">
                    <div class="feature-box">
                        <i class="fas fa-tags"></i>
                        <h5>Best Deals</h5>
                        <p class="text-muted small">Directly negotiated from owner listings to ensure you get the best market rate.</p>
                    </div>
                </div>
                <div class="col-md-4 mb-4">
                    <div class="feature-box">
                        <i class="fas fa-map-marked-alt"></i>
                        <h5>Prime Locations</h5>
                        <p class="text-muted small">Properties strategically located near major stations, top schools, and markets.</p>
                    </div>
                </div>
            </div>
        </div>

        <footer class="mega-footer">
            <div class="container">
                <div class="row">
                    <div class="col-md-4 mb-4 pe-md-5">
                        <h5 class="text-white mb-3"><i class="fas fa-building text-primary me-2"></i>Vajrai Properties</h5>
                        <p class="small text-muted" style="line-height: 1.8;">Your premier real estate partner. We specialize in helping families and businesses find the perfect property that fits their budget and lifestyle goals.</p>
                    </div>
                    <div class="col-md-4 mb-4">
                        <h5>Quick Links</h5>
                        <ul class="list-unstyled small">
                            <li><a href="/"><i class="fas fa-angle-right text-primary me-2"></i> Home</a></li>
                            <li><a href="/?category=Buy"><i class="fas fa-angle-right text-primary me-2"></i> Buy Property</a></li>
                            <li><a href="/?category=Rent"><i class="fas fa-angle-right text-primary me-2"></i> Rent Property</a></li>
                            <li><a href="/admin"><i class="fas fa-angle-right text-primary me-2"></i> Admin Login</a></li>
                        </ul>
                    </div>
                    <div class="col-md-4 mb-4">
                        <h5>Contact Us</h5>
                        <ul class="list-unstyled small">
                            <li class="mb-3 d-flex"><i class="fas fa-map-marker-alt text-primary me-3 mt-1"></i> <span>Office No 24, Galaxy Avenue,<br>Virar West - 401303</span></li>
                            <li class="mb-3 d-flex"><i class="fas fa-phone-alt text-primary me-3 mt-1"></i> <span>+91 8999338010</span></li>
                            <li class="mb-3 d-flex"><i class="fab fa-whatsapp text-primary me-3 mt-1"></i> <span>24/7 WhatsApp Support</span></li>
                        </ul>
                    </div>
                </div>
                <div class="footer-bottom d-flex flex-column flex-md-row justify-content-between align-items-center">
                    <div>© 2026 Vajrai Properties. All Rights Reserved.</div>
                    <div class="mt-2 mt-md-0">Serving Virar, Vasai & Mumbai</div>
                </div>
            </div>
        </footer>

        <a href="https://wa.me/918999338010" class="whatsapp-float" target="_blank"><i class="fab fa-whatsapp"></i></a>
    </body>
    </html>
    """

# ---------------- PROPERTY DETAILS (ALL FEATURES) ----------------
@app.get("/property/{pid}", response_class=HTMLResponse)
def property_details(pid: int, db: Session = Depends(get_db)):
    p = db.query(Property).filter(Property.id == pid).first()
    if not p: return HTMLResponse("<h1>Property Not Found</h1>", status_code=404)

    images = parse_images(p.image)
    carousel_items = ""
    for index, img_url in enumerate(images):
        active_class = "active" if index == 0 else ""
        optimized_img = optimize_url(img_url, width=800)
        carousel_items += f'<div class="carousel-item {active_class}"><img src="{optimized_img}" class="d-block w-100 rounded" style="height: 400px; object-fit: cover;" alt="Property Image"></div>'

    similar_props = db.query(Property).filter(Property.category == p.category, Property.id != p.id).limit(3).all()
    similar_html = ""
    for sp in similar_props:
        thumb = optimize_url(parse_images(sp.image)[0], width=300)
        similar_html += f"""
        <div class="col-md-4 mb-3">
            <div class="card h-100 border-0 shadow-sm">
                <a href="/property/{sp.id}"><img src="{thumb}" class="card-img-top" style="height:150px; object-fit:cover;"></a>
                <div class="card-body p-2">
                    <h6 class="card-title text-truncate">{sp.title}</h6>
                    <p class="text-success fw-bold small mb-0">₹ {sp.price}</p>
                </div>
            </div>
        </div>
        """
    if not similar_html: similar_html = "<p class='text-muted'>No other properties in this category yet.</p>"

    map_query = urllib.parse.quote(p.location)
    google_map_embed = f'<div class="map-container"><iframe src="https://maps.google.com/maps?q={map_query}&t=&z=14&ie=UTF8&iwloc=&output=embed" frameborder="0" scrolling="no" marginheight="0" marginwidth="0"></iframe></div>'
    
    video_embed = ""
    if p.video_url:
        embed_link = get_youtube_embed(p.video_url)
        if embed_link:
            video_embed = f'<div class="video-container"><iframe src="{embed_link}" allowfullscreen></iframe></div>'

    status_badge = ""
    if p.status == "Sold": status_badge = '<span class="badge bg-danger ms-2">SOLD OUT</span>'
    elif p.status == "Rented": status_badge = '<span class="badge bg-primary ms-2">RENTED</span>'

    return f"""
    <!DOCTYPE html><html>{HTML_HEAD}<body>
        <nav class="navbar navbar-expand-lg"><div class="container"><a class="navbar-brand" href="/">Vajrai Properties</a><a href="/" class="btn btn-secondary btn-sm rounded-pill px-3">Back</a></div></nav>
        
        <div class="container mt-4">
            <div class="row">
                <div class="col-md-8">
                    <div id="propCarousel" class="carousel slide mb-4" data-bs-ride="carousel">
                        <div class="carousel-inner">{carousel_items}</div>
                        <button class="carousel-control-prev" type="button" data-bs-target="#propCarousel" data-bs-slide="prev"><span class="carousel-control-prev-icon"></span></button>
                        <button class="carousel-control-next" type="button" data-bs-target="#propCarousel" data-bs-slide="next"><span class="carousel-control-next-icon"></span></button>
                    </div>

                    <ul class="nav nav-tabs" id="myTab" role="tablist">
                        <li class="nav-item"><button class="nav-link active" data-bs-toggle="tab" data-bs-target="#details">Details</button></li>
                        <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#map">Map</button></li>
                        { '<li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#video">Video Tour</button></li>' if video_embed else '' }
                    </ul>
                    
                    <div class="tab-content mt-3" id="myTabContent">
                        <div class="tab-pane fade show active" id="details">
                            <p style="white-space: pre-line; color:#555;">{p.description}</p>
                        </div>
                        <div class="tab-pane fade" id="map">{google_map_embed}</div>
                        <div class="tab-pane fade" id="video">{video_embed}</div>
                    </div>

                    <div class="mt-5">
                        <h5 class="mb-3 border-bottom pb-2">Similar Properties</h5>
                        <div class="row">{similar_html}</div>
                    </div>
                </div>

                <div class="col-md-4">
                    <div class="card shadow-sm p-4 border-0 mb-4">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span class="badge bg-dark">{p.category}</span> {status_badge}
                        </div>
                        <h2>{p.title}</h2>
                        <h3 class="text-success fw-bold mb-3">₹ {p.price}</h3>
                        <div class="d-none d-md-block">
                            <a href="https://wa.me/918999338010?text=Hi, I am interested in {p.title}" class="btn btn-success w-100 mb-2 btn-lg"><i class="fab fa-whatsapp"></i> WhatsApp</a>
                            <a href="tel:+918999338010" class="btn btn-outline-dark w-100"><i class="fas fa-phone"></i> Call Agent</a>
                        </div>
                    </div>

                    <div class="calc-box">
                        <h5 class="text-center mb-3"><i class="fas fa-calculator"></i> EMI Calculator</h5>
                        <label>Loan Amount (₹)</label>
                        <input type="number" id="loanAmt" class="form-control mb-2" placeholder="e.g. 5000000">
                        <label>Interest Rate (%)</label>
                        <input type="number" id="intRate" class="form-control mb-2" value="8.5" step="0.1">
                        <label>Tenure (Years)</label>
                        <input type="number" id="years" class="form-control mb-3" value="20">
                        <button onclick="calcEMI()" class="btn btn-primary w-100 btn-sm">Calculate</button>
                        <div id="emiResult" class="calc-result"></div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            function calcEMI() {{
                let p = document.getElementById('loanAmt').value;
                let r = document.getElementById('intRate').value / 12 / 100;
                let n = document.getElementById('years').value * 12;
                if(p && r && n) {{
                    let emi = p * r * (Math.pow(1+r,n) / (Math.pow(1+r,n)-1));
                    document.getElementById('emiResult').innerText = "₹ " + Math.round(emi).toLocaleString();
                }}
            }}
        </script>

        <div class="d-md-none mobile-bottom-nav">
            <a href="tel:+918999338010" class="btn btn-outline-dark w-50 me-2"><i class="fas fa-phone"></i> Call</a>
            <a href="https://wa.me/918999338010?text=Interested in {p.title}" class="btn btn-success w-50"><i class="fab fa-whatsapp"></i> WhatsApp</a>
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
    <label class="form-label">Title</label><input name="title" class="form-control mb-2" required>
    <div class="row mb-2"><div class="col"><label class="form-label">Type</label><select name="category" class="form-select"><option value="Buy">Sell</option><option value="Rent">Rent</option></select></div>
    <div class="col"><label class="form-label">Price</label><input name="price" class="form-control" required></div></div>
    <label class="form-label">Location</label><input name="location" class="form-control mb-2" required>
    <label class="form-label">YouTube Video Link (Optional)</label><input name="video_url" class="form-control mb-2" placeholder="https://youtu.be/...">
    <label class="form-label">Description</label><textarea name="description" class="form-control mb-3" rows="4"></textarea>
    <label class="fw-bold form-label">Photos (Max 5)</label><input type="file" name="image_files" class="form-control mb-3" accept="image/*" multiple required>
    <button type="submit" class="btn btn-primary w-100">Submit</button>
    </form></div></div></body></html>
    """

@app.post("/add-property")
async def save_property(request: Request, title: str = Form(...), location: str = Form(...), price: str = Form(...), description: str = Form(...), category: str = Form(...), video_url: Optional[str] = Form(None), image_files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    if request.cookies.get("admin_token") != "logged_in": return RedirectResponse(url="/admin", status_code=303)
    uploaded_urls = []
    for file in image_files:
        try:
            res = cloudinary.uploader.upload(file.file)
            uploaded_urls.append(res.get("url"))
        except: pass
    new_prop = Property(title=title, location=location, price=price, description=description, image=json.dumps(uploaded_urls), category=category, status="Available", video_url=video_url)
    db.add(new_prop)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

# ---------------- EDIT PROPERTY ----------------
@app.get("/edit-property/{pid}", response_class=HTMLResponse)
def edit_property_form(pid: int, request: Request, db: Session = Depends(get_db)):
    if request.cookies.get("admin_token") != "logged_in": return RedirectResponse(url="/admin", status_code=303)
    p = db.query(Property).filter(Property.id == pid).first()
    
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
    <label>YouTube Video Link</label><input name="video_url" class="form-control mb-2" value="{p.video_url or ''}">
    <label>Description</label><textarea name="description" class="form-control mb-3" rows="5">{p.description}</textarea>
    <button type="submit" class="btn btn-warning w-100">Update</button>
    </form></div></div></body></html>
    """

@app.post("/edit-property/{pid}")
def update_property(pid: int, request: Request, title: str = Form(...), price: str = Form(...), location: str = Form(...), description: str = Form(...), status: str = Form(...), video_url: Optional[str] = Form(None), db: Session = Depends(get_db)):
    if request.cookies.get("admin_token") != "logged_in": return RedirectResponse(url="/admin", status_code=303)
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

# ---------------- DELETE & ADMIN ----------------
@app.get("/delete-property/{pid}")
def delete_property(pid: int, request: Request, db: Session = Depends(get_db)):
    if request.cookies.get("admin_token") != "logged_in": return RedirectResponse(url="/admin", status_code=303)
    prop = db.query(Property).filter(Property.id == pid).first()
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

# ---------------- RESET DB ----------------
@app.get("/reset-db", response_class=HTMLResponse)
def reset_database():
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    return "<h1 style='color:green; text-align:center; margin-top:50px;'>Database Reset Successful!<br><a href='/'>Go Home</a></h1>"