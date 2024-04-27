from fastapi import Response, Request
from fastapi import Depends, FastAPI, HTTPException, status
from datetime import datetime, timedelta
from typing import List, Union
from fastapi import FastAPI
from fastapi import APIRouter, status
from pydantic import BaseModel
import time
import uuid
import re
import jwt
from apps.web.models.auths import (
    SigninForm,
    SignupForm,
    UpdateProfileForm,
    UpdatePasswordForm,
    UserResponse,
    SigninResponse,
    Auths,
)
from apps.web.models.users import Users

from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)
from utils.utils import (
    get_password_hash,
    get_current_user,
    get_admin_user,
    create_token)
   # send_verification_email,

from utils.misc import parse_duration, validate_email_format
from constants import ERROR_MESSAGES

router = APIRouter()


from fastapi import FastAPI
from fastapi.responses import RedirectResponse

app = FastAPI()

############################
# GoogleAuth
############################

from pydantic import BaseModel

class TokenSchema(BaseModel):
    token: str

import config

SECRET_KEY = config.WEBUI_SECRET_KEY
ALGORITHM = "HS256"

def create_access_token(user_id: str):
    
    to_encode = user_id.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/auth/google")
async def google_auth(token_data: TokenSchema):
    token = token_data.token
    print(f"Received token: {token}") 
    
    try:
        CLIENT_ID = "763749380527-s493gmjqulracsgaa4ae4umr2pj8k7kv.apps.googleusercontent.com"
        print("Verifying token...")  

       
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        print("Decoded token:", decoded_token)        
        email = decoded_token.get('email')
        if not email:
            print("Email not found in token.")
            raise HTTPException(status_code=400, detail="Email not found in token.")
        
        print(f"Extracted email: {email}")


        print(f"Fetching or creating user by email: {email}")

        print(f"Fetching user by email: {email}")
        user = Users.get_user_by_email(email)
        print(f"User fetched: {user}") 

        if user is None:

            print(f"Creating new user: {email}")
            user = Auths.insert_new_auth(email.lower(),password=None,name=None,role="user")
            print(user)

       
        print(f"Generating JWT for user: {user.id}")
        joken = create_access_token(
            user['id']
        )
        print(f"JWT Token: {jwt_token}")  
        return {"jwt_token": joken}
    except ValueError as e:
        print(f"Token verification failed: {e}")  
        raise HTTPException(status_code=400, detail="Invalid Google token.")


@router.get("/test-redirect")
async def test_redirect():
    return RedirectResponse("http://localhost:5173")

############################
# Email Verification
############################

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from itsdangerous import URLSafeTimedSerializer as Serializer
from config import MAIL_CONFIG
import config
from fastapi.responses import RedirectResponse
# Email verification setup
# Configuration for the email client
conf = ConnectionConfig(
    MAIL_USERNAME="legalaxess@gmail.com", 
    MAIL_PASSWORD="upywyvkgulpqvrmb",  
    MAIL_FROM="legalaxess@gmail.com",  
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",  
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)


fm = FastMail(conf)

SECRET_KEY = "a9354d435ecbe043fde4ef6f92b65d32a9e5cc7ec8be8e117823453f627c6ad1"
serializer = Serializer(SECRET_KEY)

def generate_verification_token(email):

    return serializer.dumps(email, salt="email-verify")

def verify_token(token, expiration=3600):
    try:
        email = serializer.loads(
            token,
            salt="email-verify",
            max_age=expiration
        )
    except:
        return False
    return email

async def send_verification_email(email):
    token = generate_verification_token(email)
    verification_link = f"https://chat.techpeek.in/api/v1/auths/verify/{token}"

    message = MessageSchema(
        subject="Email Verification",
        recipients=[email],
        body=f"Please click on the link to verify your email: {verification_link}",
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)

from fastapi import BackgroundTasks

@router.get("/verify/{token}")
async def verify_email(token: str):
    email = verify_token(token)
    print(f"Verifying token: {token}")
    if not email:
        print("Token verification failed.")
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = Users.get_user_by_email(email)
    if user:
        Users.verify_user(email)
        print(f"User {email} verified successfully.")
        return RedirectResponse("https://chat.techpeek.in")
    else:
        raise HTTPException(status_code=404, detail="User not found")



############################
# GetSessionUser
############################


@router.get("/", response_model=UserResponse)
async def get_session_user(user=Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "profile_image_url": user.profile_image_url,
    }


############################
# Update Profile
############################


@router.post("/update/profile", response_model=UserResponse)
async def update_profile(
    form_data: UpdateProfileForm, session_user=Depends(get_current_user)
):
    if session_user:
        user = Users.update_user_by_id(
            session_user.id,
            {"profile_image_url": form_data.profile_image_url, "name": form_data.name},
        )
        if user:
            return user
        else:
            raise HTTPException(400, detail=ERROR_MESSAGES.DEFAULT())
    else:
        raise HTTPException(400, detail=ERROR_MESSAGES.INVALID_CRED)


############################
# Update Password
############################


@router.post("/update/password", response_model=bool)
async def update_password(
    form_data: UpdatePasswordForm, session_user=Depends(get_current_user)
):
    if session_user:
        user = Auths.authenticate_user(session_user.email, form_data.password)

        if user:
            hashed = get_password_hash(form_data.new_password)
            return Auths.update_user_password_by_id(user.id, hashed)
        else:
            raise HTTPException(400, detail=ERROR_MESSAGES.INVALID_PASSWORD)
    else:
        raise HTTPException(400, detail=ERROR_MESSAGES.INVALID_CRED)


############################
# SignIn
############################


@router.post("/signin", response_model=SigninResponse)
async def signin(request: Request, form_data: SigninForm):
    user = Auths.authenticate_user(form_data.email.lower(), form_data.password)
    if user:
        token = create_token(
            data={"id": user.id},
            expires_delta=parse_duration(request.app.state.JWT_EXPIRES_IN),
        )

        return {
            "token": token,
            "token_type": "Bearer",
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "profile_image_url": user.profile_image_url,
        }
    else:
        raise HTTPException(400, detail=ERROR_MESSAGES.INVALID_CRED)


############################
# SignUp
############################


@router.post("/signup", response_model=SigninResponse)
async def signup(request: Request, form_data: SignupForm, background_tasks: BackgroundTasks):
    if not request.app.state.ENABLE_SIGNUP:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail=ERROR_MESSAGES.ACCESS_PROHIBITED
        )

    if not validate_email_format(form_data.email.lower()):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail=ERROR_MESSAGES.INVALID_EMAIL_FORMAT
        )

    if Users.get_user_by_email(form_data.email.lower()):
        raise HTTPException(400, detail=ERROR_MESSAGES.EMAIL_TAKEN)

    try:
        role = (
            "admin"
            if Users.get_num_users() == 0
            else request.app.state.DEFAULT_USER_ROLE
        )
        hashed = get_password_hash(form_data.password)
        user = Auths.insert_new_auth(
            form_data.email.lower(), hashed, form_data.name, role
        )

        if user:
            background_tasks.add_task(send_verification_email, form_data.email.lower())
            token = create_token(
                data={"id": user.id},
                expires_delta=parse_duration(request.app.state.JWT_EXPIRES_IN),
            )
            # response.set_cookie(key='token', value=token, httponly=True)
            return {
                "token": token,
                "token_type": "Bearer",
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "profile_image_url": user.profile_image_url,
            }
        else:
            raise HTTPException(500, detail=ERROR_MESSAGES.CREATE_USER_ERROR)
    except Exception as err:
        raise HTTPException(500, detail=ERROR_MESSAGES.DEFAULT(err))


############################
# ToggleSignUp
############################


@router.get("/signup/enabled", response_model=bool)
async def get_sign_up_status(request: Request, user=Depends(get_admin_user)):
    return request.app.state.ENABLE_SIGNUP


@router.get("/signup/enabled/toggle", response_model=bool)
async def toggle_sign_up(request: Request, user=Depends(get_admin_user)):
    request.app.state.ENABLE_SIGNUP = not request.app.state.ENABLE_SIGNUP
    return request.app.state.ENABLE_SIGNUP


############################
# Default User Role
############################


@router.get("/signup/user/role")
async def get_default_user_role(request: Request, user=Depends(get_admin_user)):
    return request.app.state.DEFAULT_USER_ROLE


class UpdateRoleForm(BaseModel):
    role: str


@router.post("/signup/user/role")
async def update_default_user_role(
    request: Request, form_data: UpdateRoleForm, user=Depends(get_admin_user)
):
    if form_data.role in ["pending", "user", "admin"]:
        request.app.state.DEFAULT_USER_ROLE = form_data.role
    return request.app.state.DEFAULT_USER_ROLE


############################
# JWT Expiration
############################


@router.get("/token/expires")
async def get_token_expires_duration(request: Request, user=Depends(get_admin_user)):
    return request.app.state.JWT_EXPIRES_IN


class UpdateJWTExpiresDurationForm(BaseModel):
    duration: str


@router.post("/token/expires/update")
async def update_token_expires_duration(
    request: Request,
    form_data: UpdateJWTExpiresDurationForm,
    user=Depends(get_admin_user),
):
    pattern = r"^(-1|0|(-?\d+(\.\d+)?)(ms|s|m|h|d|w))$"

    # Check if the input string matches the pattern
    if re.match(pattern, form_data.duration):
        request.app.state.JWT_EXPIRES_IN = form_data.duration
        return request.app.state.JWT_EXPIRES_IN
    else:
        return request.app.state.JWT_EXPIRES_IN
