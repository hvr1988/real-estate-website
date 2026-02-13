from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse

router = APIRouter()

# --- ADMIN CREDENTIALS ---
ADMIN_USER = "vajrai"
ADMIN_PASS = "12345"

# ---------------- LOGIN LOGIC ----------------
@router.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        # ✅ Success! 
        # 1. Redirect to Home Page
        response = RedirectResponse(url="/", status_code=303)
        # 2. Set the "VIP Badge" (Cookie) so the website remembers you
        response.set_cookie(key="admin_token", value="logged_in")
        return response
    else:
        # ❌ Failed! Redirect back to login with error
        return RedirectResponse(url="/admin?error=Invalid Credentials", status_code=303)

# ---------------- LOGOUT LOGIC ----------------
@router.get("/logout")
def logout():
    # 1. Go to Home Page
    response = RedirectResponse(url="/", status_code=303)
    # 2. Remove the "VIP Badge" (Delete Cookie)
    response.delete_cookie("admin_token")
    return response