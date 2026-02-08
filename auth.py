from fastapi import APIRouter, Depends, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from database import SessionLocal
import models

router = APIRouter()

# DB connection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Login page
@router.get("/admin", response_class=HTMLResponse)
def login_form():
    return """
    <h2>Admin Login</h2>
    <form method='post'>
    Username: <input name='username'><br><br>
    Password: <input name='password' type='password'><br><br>
    <button type='submit'>Login</button>
    </form>
    """

# Login check
@router.post("/admin", response_class=HTMLResponse)
def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.Admin).filter(models.Admin.username == username).first()

    if user and user.password == password:
        return """
        <h1>🏢 Admin Dashboard</h1>
        <hr>
        <a href='/add-property'>➕ Add Property</a><br><br>
        <a href='/view-property'>📋 View Properties</a><br><br>
        <a href='/'>🌐 Visit Website</a>
        """
    else:
        return "<h3>Invalid login</h3>"
