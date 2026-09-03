import os
from fastapi import Depends, FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from fastapi.responses import RedirectResponse
import uvicorn
import pprint

from database import handle_user_login_data, init_db, print_database_info, get_data_field

init_db()  # Initialize the database

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
    allow_origins=["http://localhost:3000"],
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
    # This origin MUST match the frontend origin, otherwise the cookies
    # will NOT SET for the frontend!!!!!
    redirect_uri = "http://localhost:8000/auth/callback" 
    return await oauth.github.authorize_redirect(request, redirect_uri)

#################################################

# Recieving end from the eternal github login page
@app.get("/auth/callback")
async def auth_callback(request: Request):
    try:
        # Ask github to validate the login token and return an 
        # authentication token
        auth_token = await oauth.github.authorize_access_token(request)

        # With the auth token, ask github for information about user
        response = await oauth.github.get("user", token=auth_token)
        profile_info = response.json()

        # print("---------- PROFILE INFO ----------")
        # pprint.pprint(profile_info)
        # print("----------------------------------")

        # If the email is private, we need to explicitly ask for an email
        # to recover any information
        if not profile_info.get("email"):
            email_resp = await oauth.github.get("user/emails", token=auth_token)
            emails = email_resp.json()
            for email in emails:
                if email.get("primary") and email.get("verified"):
                    profile_info["email"] = email.get("email")
                    break

        # store data in session cookie
        db_user = handle_user_login_data(profile_info)

        # store user data in session coockie
        request.session["user"] = db_user

        # Debug display info
        request.session["user"] = {
            "id": profile_info.get("id"),
            "username": profile_info.get("login"),
            "name": profile_info.get("name"),
            "avatar_url": profile_info.get("avatar_url")
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
def get_hello(user: dict = Depends(get_current_user)):

    user_email = get_data_field(user_id=1, field_name="email")

    return {"message": f"Hello, {user_email}!"}

#################################################

@app.get("/health")
def health_status():
    return {"status": "ok"}

#################################################

@app.get("/api/database")
def print_database():
    return print_database_info()

#################################################

# Launch the backend server apon startup of the application
if __name__ == "__main__":
    HOST = "127.0.0.1"
    #HOST="localhost"
    PORT = 8000
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)