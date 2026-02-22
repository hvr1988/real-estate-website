from fastapi import APIRouter, Form, Response, Request
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter()

ADMIN_USER = "vajrai"
ADMIN_PASS = "12345"

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Login | Vajrai Properties</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            body { font-family: 'Poppins', sans-serif; background-color: #f8fafc; height: 100vh; display: flex; align-items: center; justify-content: center; margin: 0; }
            .login-card { background: white; padding: 40px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); width: 100%; max-width: 400px; text-align: center; border: 1px solid #e2e8f0; }
            .btn-primary { background-color: #0f172a; border: none; }
            .btn-primary:hover { background-color: #1e293b; }
        </style>
    </head>
    <body>
        <div class="login-card mx-3">
            <h3 class="fw-bold mb-4" style="color:#0f172a;">🏢 Vajrai Admin</h3>
            <form action="/login" method="post">
                <input name="username" class="form-control mb-3 p-3 bg-light border-0" placeholder="Username" required>
                <input type="password" name="password" class="form-control mb-4 p-3 bg-light border-0" placeholder="Password" required>
                <button type="submit" class="btn btn-primary w-100 p-3 fw-bold">Login to Dashboard</button>
            </form>
            <a href="/" class="d-block mt-4 text-muted text-decoration-none small">← Back to Website</a>
        </div>
    </body>
    </html>
    """

@router.post("/login")
def login_check(response: Response, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        # Create a redirect response to the new dashboard
        redirect = RedirectResponse(url="/dashboard", status_code=303)
        # Set a secure cookie so main.py knows we are admin
        redirect.set_cookie(key="admin_token", value="logged_in", httponly=True)
        return redirect
    else:
        return HTMLResponse("<h3 style='color:red; text-align:center; margin-top:50px; font-family:sans-serif;'>❌ Wrong login details.</h3><div style='text-align:center;'><a href='/login'>Try again</a></div>")

@router.get("/logout")
def logout():
    redirect = RedirectResponse(url="/", status_code=303)
    redirect.delete_cookie("admin_token")
    return redirect