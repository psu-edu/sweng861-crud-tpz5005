import os
import logging
from fastapi import Depends, FastAPI, Request, HTTPException, status, Body, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from fastapi.responses import RedirectResponse, JSONResponse
import uvicorn
import pprint
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
import httpx
import json
import sqlite3
from cachetools import TTLCache, cached
from cachetools.keys import hashkey

from database import handle_user_login_data, init_db, print_database_info, get_data_field
from osrsdatabase import init_osrs_db, create_item, read_item, update_item, delete_item, get_all_ids

load_dotenv() # load keys into env

init_db()  # Initialize the database
init_osrs_db() # initialize the osrs database


# Create rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create a cache 50 items, 60 second expiration
#price_cache = TTLCache(maxsize=50, ttl=60)
#id_cache = TTLCache(maxsize=50, ttl=60)

# A gateway for OSRS database specific endpoints
router = APIRouter(
    prefix="/api/osrs/database",
    tags=["OSRS database gateway"]
)

# Create logger
# TODO: maybe astract this out to another script
logging.basicConfig(level=logging.INFO)
logger=logging.getLogger(__name__)

app = FastAPI(
    title="SWENG861 Assignment API",
    description="A front and backend server used to implement weekly assignments",
    version="0.3"
)

# set up a limiter for log in
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Authlib middleware
# @info: used to encrypt sessiond ata
app.add_middleware(SessionMiddleware, 
                   secret_key="secret_encryption_key",
                   same_site="lax",
                   https_only=True)

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","https://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"])

# activate the router
app.include_router(router)

# instantiate authentication object
oauth = OAuth()

# I will use github, as that is used commonly for SWENG861
oauth.register(
    name="github",
    client_id=os.getenv("GITHUB_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email"})



# Authentication verification helper function
#-------------------------------------------------------------------#
async def require_auth(request: Request):
#-------------------------------------------------------------------#
    # get the user info
    user = request.session.get("user")

    # if its null/failure throw an error
    if not user:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED,
                            detail="Authentication access token is required")

    return user


# Exception handler for excessive log in attempts
@app.exception_handler(RateLimitExceeded)
#-------------------------------------------------------------------#
async def handle_login_rate_exception(request: Request, 
                                      exc: RateLimitExceeded):
#-------------------------------------------------------------------#
    # get some info from the client
    client_ip = request.client.host

    # log into
    logger.warning(f"Excessive login attempts from: {client_ip}")

    # pretty sure code 429 is the right one here
    return JSONResponse(
        status_code=429,
        content={"detail": "Login rate exceeded. 5 log ins allowed per minute."}
    )


# @info: Validation function that checks if data exists and if its of 
#        type JSON
#-------------------------------------------------------------------#
async def validate_data(data):
#-------------------------------------------------------------------#
    # check if the data is null
    if data is None:
        return False

    if isinstance(data, (list, dict)) and len(data) == 0:
        return False
    
    # check if the data is in json format
    if isinstance(data, str):
        try:
            json.loads(data)
            return True
        except ValueError:
            return False

    # if its good, return true
    return True


#################################################


# Service Provider login
# @info: This is the endpoint that re-directs the user to the external
#        github login page
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@app.get("/auth/login")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@limiter.limit("5/minute") # Only 5 logins per minute
async def login(request: Request):
    # This redirect origin MUST match the frontend origin, otherwise 
    # the cookies will NOT SET for the frontend!!!!!
    redirect_uri = "https://localhost:8000/auth/callback" 
    return await oauth.github.authorize_redirect(request, redirect_uri)


# Recieving end from the eternal github login page
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@app.get("/auth/callback")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
async def auth_callback(request: Request):
    try:
        # Ask github to validate the login token and return an 
        # authentication token
        auth_token = await oauth.github.authorize_access_token(request)

        print("---------- AUTHENTICATION INFO ----------")
        pprint.pprint(auth_token)
        print("----------------------------------")

        # With the auth token, ask github for information about user
        response_type = await oauth.github.get("user", token=auth_token)
        profile_info = response_type.json()

        print("---------- PROFILE INFO ----------")
        pprint.pprint(profile_info)
        print("----------------------------------")

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
        return RedirectResponse(url="https://localhost:3000/")

    # Throw debug error
    except Exception as error:
        raise HTTPException(status_code=400, detail="ERROR: Authentication failed")


# Get active user data
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@app.get("/api/user")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
async def get_active_user(request: Request):
    user = request.session.get("user")
    if not user:
        return {"authenticated": False}
    return {"authenticated": True, "user": user}


# Logout user
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@app.get("/auth/logout")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="https://localhost:3000/")


# Authentication required
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@app.get("/api/hello")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
def get_hello(request: Request, user: dict = Depends(require_auth)):
 
    session_userInfo = request.session.get("user")
    username = session_userInfo.get("username")
    
    user_email = get_data_field(user_id=1, field_name="email")

    return {"message": f"Hello, {username}@{user_email}!"}


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@app.get("/health")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
def health_status(user: dict = Depends(require_auth)):
    return {"status": "ok"}


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@app.get("/api/runescape/price")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
#@cached(price_cache) # cache the price
async def get_item_price(user: dict = Depends(require_auth)):

    # In the game, each item has a developer-set id
    # This item's id is 1333
    item_id=1333

    # In order to use Jagex's official servers, you have to pay
    # as an alternative i will use the offical wiki, which updates less often
    # and returns less info
    map_url = "https://prices.runescape.wiki/api/v1/osrs/mapping" 

    headers = {
        "User-Agent": "Penn-State-Student-Project"
    }

    async with httpx.AsyncClient() as client:
        # get a response from the Jagex servers
        response = await client.get(map_url, headers=headers)

        if response.status_code != 200:
            raise HTTPException(status_code= response.status_code, detail="Failed to fetch OSRS data")

        # try to turn the response into a json
        data = response.json()

        # Validate the data
        await validate_data(data)

        item_data = {}

        #parse the master list of items
        for item in data:
            #find the one we're looking for
            if item.get("id") == item_id:
                item_data = item
                break

        name = item_data.get("name")
        id = item_data.get("id")
        price = item_data.get("value")
        
        # insert it into the database
        create_item(item_id=id, item_name=name, item_value=price)

        # print("---------- data INFO ----------")
        # pprint.pprint(item_data)
        # print("----------------------------------")

        # item_data = data.get("data", {}).get(str(item_id), {})

        return {
            "item": "Rune Scimitar",
            "id": item_id,
            "price": item_data
        }

# @info: OSRS database POST function
# @param item_id - the 4 digit itme id 
# @param item_name - the name of the item
# @param item_value - the current traded price of the 
#                     item
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@router.post("/create",
             summary="OSRS database Create endpoint")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@limiter.limit("1/5seconds") # Only 1 create every 5 seconds
def osrs_database_create(request: Request,
                         item_id: int = Body(...), 
                         item_name: str = Body(...), 
                         item_value:int = Body(...),
                         user: dict = Depends(require_auth)):
    try:
        # Create the item
        create_item(item_id, item_name, item_value)

    # If the ID already exists
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=400,
            detail=f"Item with ID: {item_id} already in database"
        )
    # if something unknown happens
    except sqlite3.Error as err:
        raise HTTPException(
            status_code=500,
            detail="Unexpected Error"
        )

    return {
        "status": "success",
        "message": "Successfully created item"
    }


# @info: Debug helper function to print the user
#        database content
# @param item_id - the 4 digit id of the item
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@router.get("/read/{item_id}",
            summary="OSRS database Read endpoint")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@limiter.limit("1/3seconds") # Only 1 read every 3 seconds
def osrs_database_read(request: Request,
                       item_id: int, 
                       user: dict = Depends(require_auth)):
    item = read_item(item_id)

    # make sure it exists
    if not item:
        raise HTTPException(status_code=404, detail="Item not found in database")
    
    return item 


# @info: Update item in database endpoint
# @param item_id - the 4 digit item id 
# @param fields - the fields to be updated
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@router.put("/update/{item_id}",
          summary="OSRS database Update endpoint")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@limiter.limit("1/5seconds") # Only 1 update every 5 seconds
def osrs_database_update(request: Request,
                         item_id: int, 
                         fields: dict = Body(...),
                         user: dict = Depends(require_auth)):
    current_item = read_item(item_id)

    # make sure it exists
    if not current_item:
        raise HTTPException(status_code=404, detail="Item not found in database")

    # if it does exist, update the data
    update_item(item_id, fields)

    return {
        "status": "success",
        "message": "Item's data successfully updated"
    } 


# @info: Delete endpoint for the OSRS database
# @param item_id - the 4 digit id 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@router.delete("/delete/{item_id}",
                summary="OSRS database Delete endpoint")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@limiter.limit("1/5seconds") # Only 1 delete every 5 seconds
def osrs_database_delete(request: Request,
                         item_id: int, 
                         user: dict = Depends(require_auth)):
    current_item = read_item(item_id)

    # it it doesnt exist, throw an error
    if not current_item:
        raise HTTPException(
            status_code=404,
            detail=f"Item with ID: {item_id} does not exist in OSRS database"
        )

    # if it does, delete it
    delete_item(item_id)
    return {
        "status": "success",
        "message": "Item successfully deleted"
    }


# @info: Debug helper function to print the current 
#        OSRS database IDs
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@router.get("/ids",
            summary="OSRS database IDs endpoint")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@limiter.limit("10/seconds") # This needs to be higher, so 10 every second
#@cached(id_cache, key=lambda item_id, **kwargs: hashkey(item_id)) # id cache
def osrs_database_registered_ids(request: Request,
                                 user: dict = Depends(require_auth)):
    # Get the current IDs
    all_current_ids = get_all_ids()

    # make sure it exists
    if not all_current_ids:
        raise HTTPException(status_code=404, detail="No IDs were found in OSRS database")
    
    return {
        "ids": all_current_ids
    }

# @info: Debug helper function to print the user
#        database content
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
@app.get("/api/database")
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
def print_database(user: dict = Depends(require_auth)):
    return print_database_info()


#################################################


# Launch the backend server apon startup of the application
if __name__ == "__main__":
    HOST = "127.0.0.1"
    PORT = 8000
    uvicorn.run("main:app", 
                host=HOST, 
                port=PORT, 
                reload=True,
                ssl_certfile="cert.pem",
                ssl_keyfile="key.pem")