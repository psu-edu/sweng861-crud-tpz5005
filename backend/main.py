import os
from fastapi import Depends, FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from fastapi.responses import RedirectResponse
import uvicorn

app = FastAPI()

# Authlib middleware
# @info: used to encrypt sessiond ata
app.add_middleware(SessionMiddleware, 
                   secret_key="secret_encryption_key",
                   same_site="lax",
                   https_only=False)

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
                   "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])

# instantiate authentication object
oauth = OAuth()

# I will use github, as that is used commonly for SWENG861
oauth.register(
    name="github",
    client_id="Ov23lisvubhy2pCXWy6l", # got this from github
    client_secret="a5aaa80b59c66ae3a05ba706eadafc0ef9e8627e", # generated from github
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email"})

# Authentication verification helper function
#-----------------------------------------------#
async def get_current_user(request: Request):
#-----------------------------------------------#
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code = 401,
                            detail="Authentication required for this endpoint")
    return user

#################################################

# Service Provider login
# @info: This is the endpoint that re-directs the user to the external
#        github login page
@app.get("/auth/login")
async def login(request: Request):
    redirect_uri = "http://127.0.0.1:8000/auth/callback"
    return await oauth.github.authorize_redirect(request, redirect_uri)

#################################################

# Recieving end from the eternal github login page
@app.get("/auth/callback")
async def auth_callback(request: Request):
    try:
        auth_token = await oauth.github.authorize_access_token(request)

        response = await oauth.github.get("user", token=auth_token)
        profile = response.json()

        # store data in session cookie
        request.session["user"] = {
            "id": profile.get("id"),
            "username": profile.get("login"),
            "name": profile.get("name"),
            "avatar_url": profile.get("avatar_url")
        }

        # if we are susseccful, redirect back to the frontend
        return RedirectResponse(url="http://localhost:3000/")

    # Throw debug error
    except Exception as error:
        raise HTTPException(status_code=400, detail="ERROR: Authentication failed")

#################################################

# Get active user data
@app.get("/api/user")
async def get_active_user(request: Request):
    user = request.session.get("user")
    if not user:
        return {"authenticated": False}
    return {"authenticated": True, "user": user}

#################################################

# Logout user
@app.get("/auth/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="http://localhost:3000/")

#################################################

@app.get("/api/hello")
def get_hello():
    return {"message": "Hello World!"}

#################################################

@app.get("/health")
def health_status(user: dict = Depends(get_current_user)):
    return {"status": "ok"}

#################################################

# Launch the backend server apon startup of the application
if __name__ == "__main__":
    HOST = "127.0.0.1"
    #HOST = "0.0.0.0"
    PORT = 8000
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)