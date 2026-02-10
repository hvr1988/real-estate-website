from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse

router = APIRouter()

ADMIN_USER = "vajrai"
ADMIN_PASS = "12345"

# ---------------- LOGIN PAGE ----------------
@router.get("/login", response_class=HTMLResponse)
def login_page():
    return """
    <h2>🔐 Admin Login - Vajrai Properties</h2>
    <form method='post'>
    Username:<br>
    <input name='username'><br><br>
    Password:<br>
    <input type='password' name='password'><br><br>
    <button type='submit'>Login</button>
    </form>
    """

# ---------------- LOGIN CHECK ----------------
@router.post("/login", response_class=HTMLResponse)
def login_check(username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        return """
        <h2>Welcome Admin</h2>
        <a href='/add-property'>➕ Add Property</a><br><br>
        <a href='/view-property'>📋 View Properties</a><br><br>
        <a href='/'>🏠 Go Website</a>
        """
    else:
        return "<h3>❌ Wrong login</h3><a href='/login'>Try again</a>"
