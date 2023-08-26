from flask import Flask,redirect,jsonify
from os import environ
from flask_jwt_extended import JWTManager
from flasgger import Swagger,swag_from
from src.auth import auth
from src.bookmarks import bookmarks
from src.database import db,Bookmark
from src.constants.http_status_codes import  HTTP_200_OK,HTTP_500_INTERNAL_SERVER_ERROR,HTTP_404_NOT_FOUND
from src.config.swapper import swagger_config,template

def create_app(test_config=None):
    app = Flask(__name__,instance_relative_config=True)

    if test_config is None:
        app.config.from_mapping(SECRET_KEY=environ.get('SECRET_KEY'),SQLALCHEMY_DATABASE_URI=environ.get('SQLALCHEMY_DB_URI'),JWT_SECRET_KEY=environ.get('JWT_SECRET_KEY')),
        SWAGGER={
            "title":"Bookmarks API",
            "uiversion":3
        }
    else:
        app.config.from_mapping(test_config)

    db.app = app
    db.init_app(app)
    JWTManager(app)
    app.register_blueprint(auth)
    app.register_blueprint(bookmarks)

    Swagger(app,config=swagger_config,template=template)
    # creating the tables

    # @app.before_f

    @app.get("/<short_url>")
    @swag_from("./docs/short_url.yaml")
    def redirect_to_url(short_url):
        try:
            bookmark = Bookmark.query.filter_by(short_url=short_url).first()
            if not bookmark:
                return jsonify({"message": "The bookmark requested is not found!!", "status": "error"}),HTTP_200_OK
            bookmark.visits = bookmark.visits + 1
            db.session.commit()
            return redirect(bookmark.url)

        except Exception as e:
            return  jsonify({"message": "Unable to redirect to the url: {str(e}", "status": "error"}),HTTP_500_INTERNAL_SERVER_ERROR

    @app.errorhandler(HTTP_404_NOT_FOUND)
    def handle_404(e):
        return jsonify({"message":"The resource you are requesting for is not found!!!","status":"error"}),HTTP_404_NOT_FOUND

    @app.errorhandler(HTTP_500_INTERNAL_SERVER_ERROR)
    def handle_500(e):
        return jsonify({"message": "Something went wrong, we are working on it to give a fix!!!", "status": "error"}), HTTP_500_INTERNAL_SERVER_ERROR

    return app
    