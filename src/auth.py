from flask import Blueprint,request,jsonify
from werkzeug.security import generate_password_hash,check_password_hash
import validators
from flasgger import swag_from
from flask_jwt_extended import create_access_token,create_refresh_token,get_jwt_identity,jwt_required
from src.database import User,db
from src.constants.http_status_codes import HTTP_400_BAD_REQUEST,HTTP_201_CREATED,HTTP_409_CONFLICT,HTTP_500_INTERNAL_SERVER_ERROR,HTTP_404_NOT_FOUND,HTTP_200_OK

auth = Blueprint("auth",__name__,url_prefix="/api/v1/auth")


@auth.post("/register")
@swag_from('./docs/auth/register.yaml')
def register():
    username = request.json.get("username","")
    password = request.json.get("password","")
    email = request.json.get("email","")

    if len(password) < 6:
        return jsonify({"message":"Password is too short, must be at least 6 characters","status":"error"}),HTTP_400_BAD_REQUEST
    
    if len(username) < 3:
        return jsonify({"message":"Username is too short, must be at least 3 characters","status":"error"}),HTTP_400_BAD_REQUEST
    
    if not username.isalnum() or " " in username:
        return jsonify({"message":"Username must be alphanumeric and doesnt contain white spaces","status":"error"}),HTTP_400_BAD_REQUEST
    
    if not validators.email(email):
        return jsonify({"message":"Email is not valid","status":"error"}),HTTP_400_BAD_REQUEST
    
    if User.query.filter_by(email=email).first() is not None:
        return jsonify({"message":"Email is already in use","status":"error"}),HTTP_409_CONFLICT
    
    if User.query.filter_by(username=username).first() is not None:
        return jsonify({"message":"Username is already in use","status":"error"}),HTTP_409_CONFLICT
    
    pwd_hash = generate_password_hash(password)
    try:
        user = User(username=username,email=email,password=pwd_hash)
        db.session.add(user)
        db.session.commit()

        return jsonify({"message":"User created successfully","status":"success"}),HTTP_201_CREATED
    except Exception as e:
        return jsonify({"message":f"Failed to create user: {str(e)}","status":"error"}),HTTP_500_INTERNAL_SERVER_ERROR
    

@auth.post("/login")
@swag_from("./docs/auth/login.yaml")
def login():
    email = request.json.get("email",'')
    password = request.json.get("password",'')

    # input validation
    if len(password) < 6:
        return jsonify({"message":"Password is too short, must be at least 6 characters","status":"error"}),HTTP_400_BAD_REQUEST
    if not validators.email(email):
        return jsonify({"message":"Email is not valid","status":"error"}),HTTP_400_BAD_REQUEST
    
    try:
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"message":"User not found","status":"error"}),HTTP_404_NOT_FOUND
        
        is_valid_pwd = check_password_hash(user.password,password)
        if not is_valid_pwd:
            return jsonify({"message":"Invalid Username/Password combination","status":"error"}),HTTP_400_BAD_REQUEST
        refresh_token = create_refresh_token(identity=user.id)
        auth_token = create_access_token(identity=user.id)
        return jsonify({
            "user":{
                "auth_token": auth_token,
                "refresh_token": refresh_token,
                "id": user.id,
                "username": user.username,
                "email": user.email
            },"message": "user authentication successful", "status": "success"
        }),HTTP_200_OK
    except Exception as e:
        return jsonify({"message":f"Failed to authenticate user: {str(e)}", "status": "error"}), HTTP_500_INTERNAL_SERVER_ERROR


@auth.get("/me")
@jwt_required()
def get_user():
    user_id = get_jwt_identity()
    try:
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({"message": "User not found", "status": "error"}),HTTP_404_NOT_FOUND
        return jsonify({"user":{"username": user.username, "email": user.email}}),HTTP_200_OK
    except Exception as e:
        return jsonify({"message":f"Failed to get user: {str(e)}","status":"error"}),HTTP_500_INTERNAL_SERVER_ERROR
    

@auth.get("/token/refresh")
@jwt_required(refresh=True)
def refresh_access_token():
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)

    return jsonify({"message": "Access token successfully generated", "status": "success", "access_token": access_token}), HTTP_200_OK
