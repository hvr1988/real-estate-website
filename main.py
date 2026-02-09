from fastapi import FastAPI, Form, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from database import engine, SessionLocal
import models
from auth import router as auth_router # Moved import to top for better style

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Include the auth router
app.include_router(auth_router)

# DB connection dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------- HOME PAGE ----------------
from fastapi.responses import HTMLResponse
from fastapi import Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ---------------- ADD PROPERTY PAGE (FORM) ----------------
@app.get("/add-property", response_class=HTMLResponse)
def add_property_form():
    return """
    <h2>Add Property</h2>
    <form action="/add-property" method="post">
        Title: <input name="title"><br><br>
        Location: <input name="location"><br><br>
        Price: <input name="price"><br><br>
        Description: <input name="description"><br><br>
        Image URL: <input name="image"><br><br>
        <button type="submit">Save Property</button>
    </form>
    """

# ---------------- SAVE PROPERTY (POST) ----------------
@app.post("/add-property", response_class=HTMLResponse)
def save_property(
    title: str = Form(...), 
    location: str = Form(...),
    price: str = Form(...), 
    description: str = Form(...),
    image: str = Form(...), 
    db: Session = Depends(get_db)
):
    # 1. Create the model object
    new_property = models.Property(
        title=title,
        location=location,
        price=price,
        description=description,
        image=image
    )

    # 2. Add to DB and Commit
    db.add(new_property)
    db.commit()
    db.refresh(new_property) # Optional: refreshes the object with new ID

    return f"<h3>Property '{title}' Added Successfully</h3><br><a href='/view-property'>View All</a>"

# ---------------- VIEW ALL PROPERTIES ----------------
@app.get("/view-property", response_class=HTMLResponse)
def view_property(db: Session = Depends(get_db)):
    # 1. Get all properties
    properties = db.query(models.Property).all()

    html = "<h1>🏢 All Properties</h1><hr>"
    
    # --- FIX STARTS HERE ---
    # The loop and return must be INSIDE the function (indented)
    for p in properties:
        html += f"""
        <div style='border:1px solid black;padding:10px;margin:10px;width:300px'>
            <h3>{p.title} (ID: {p.id})</h3>
            <img src='{p.image}' width='250'><br>
            <b>Location:</b> {p.location}<br>
            <b>Price:</b> {p.price}<br>
            <b>Description:</b> {p.description}<br><br>
            <a href='/delete-property/{p.id}' style='color:red'>❌ Delete</a>
        </div>
        """

    html += "<br><a href='/add-property'>➕ Add New Property</a>"
    
    return html 
    # --- FIX ENDS HERE ---

# ---------------- DELETE PROPERTY ----------------
@app.get("/delete-property/{pid}", response_class=HTMLResponse)
def delete_property(pid: int, db: Session = Depends(get_db)):
    property_to_delete = db.query(models.Property).filter(models.Property.id == pid).first()

    if property_to_delete:
        db.delete(property_to_delete)
        db.commit()
        return "<h3>Property Deleted</h3><br><a href='/view-property'>Back to List</a>"
    
    return "<h3>Property Not Found</h3><br><a href='/view-property'>Back to List</a>"

# ---------------- PUBLIC WEBSITE ----------------
@app.get("/properties", response_class=HTMLResponse)
def public_properties(db: Session = Depends(get_db)):

    properties = db.query(models.Property).all()

    html = """
    <html>
    <head>
    <title>Dream Properties</title>
    </head>

    <body style="font-family:Arial;background:#f4f6f8">

    <h1 style="background:#0d6efd;color:white;padding:15px">
    🏠 Dream Properties
    </h1>

    <center>
    <h2>Find Your Perfect Home</h2>
    </center>
    <hr>
    """

    for p in properties:
        html += f"""
        <div style='background:white;border-radius:10px;
        padding:15px;margin:20px;box-shadow:0px 0px 10px gray;
        width:300px;display:inline-block'>

        <img src='{p.image}' width='100%' style='border-radius:10px'><br><br>

        <h3>{p.title}</h3>
        📍 {p.location}<br>
        💰 <b>{p.price}</b><br><br>

        {p.description}<br><br>

        <a href='https://wa.me/919999999999?text=I am interested in {p.title}'
        style='background:green;color:white;padding:10px;
        text-decoration:none;border-radius:5px'>
        📞 WhatsApp Now
        </a>

        </div>
        """

    html += "</body></html>"

    return html
