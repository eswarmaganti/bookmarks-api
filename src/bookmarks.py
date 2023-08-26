from flask import Blueprint,request,jsonify
import validators
from flask_jwt_extended import  jwt_required,get_jwt_identity
from src.constants.http_status_codes import HTTP_400_BAD_REQUEST,HTTP_201_CREATED,HTTP_409_CONFLICT,HTTP_500_INTERNAL_SERVER_ERROR,HTTP_200_OK,HTTP_404_NOT_FOUND,HTTP_204_NO_CONTENT
from src.database import  Bookmark,db
bookmarks = Blueprint("bookmarks", __name__,url_prefix="/api/v1/bookmarks")


@bookmarks.route("/",methods=['POST','GET'])
@jwt_required()
def handle_bookmarks():
    user_id = get_jwt_identity()
    def create_bookmark():
        url = request.json.get("url","")
        body = request.json.get("body","")
        # validation
        if not validators.url(url):
            return  jsonify({"message":"Invalid url provided!","status":"error"}),HTTP_400_BAD_REQUEST
        try:
            is_bookmark_existed = Bookmark.query.filter_by(url=url,user_id=user_id).first()
            if is_bookmark_existed:
                return jsonify({"message": "The bookmark already created for existing url!!", "status": "error"}), HTTP_400_BAD_REQUEST

            bookmark = Bookmark(url=url,body=body,user_id=user_id)
            db.session.add(bookmark)
            db.session.commit()

            return jsonify(
                {"message": "The bookmark successfully created", "status": "error","data":{
                    "url":bookmark.url,
                    "short_url":bookmark.short_url,
                    "body":bookmark.body,
                    "visits":bookmark.visits,
                    "created_at":bookmark.created_at,
                    "updated_at":bookmark.updated_at
                }}), HTTP_201_CREATED

        except Exception as e:
            return  jsonify({"message":f"Failed to create bookmark: {str(e)}","status":"error"}),HTTP_500_INTERNAL_SERVER_ERROR

    def get_bookmarks():
        page = request.args.get("page",1,type=int)
        per_page = request.args.get("per_page",5,type=int)

        try:
            bookmarks = Bookmark.query.filter_by(user_id=user_id).paginate(page=page,per_page=per_page)

            data = [{
                "id":bm.id,
                "url":bm.url,
                "short_url":bm.short_url,
                "body":bm.body,
                "visits": bm.visits,
                "created_at":bm.created_at,
                "updated_at":bm.updated_at,
            } for bm in bookmarks.items]

            meta = {
                "page":bookmarks.page,
                "pages":bookmarks.pages,
                "total_count":bookmarks.total,
                "prev_page":bookmarks.prev_num,
                "next_page":bookmarks.next_num,
                "has_next":bookmarks.has_next,
                "has_prev":bookmarks.has_prev
            }

            return jsonify({"data":data,"meta":meta,"message":"bookmarks successfully fetched","status":"success"}),HTTP_200_OK

        except Exception as e:
            return  jsonify({"message":f"Unable to get the bookmarks: {str(e)}","status":"error"}),HTTP_500_INTERNAL_SERVER_ERROR

    if(request.method == "GET"):
        return  get_bookmarks()
    else:
        return create_bookmark()

@bookmarks.get("/<int:id>")
@jwt_required()
def get_bookmark(id):
    user_id = get_jwt_identity()
    try:
        bookmark = Bookmark.query.filter_by(id=id,user_id=user_id).first()
        if not bookmark:
            return jsonify({"message":"The bookmark is not found!","status":"error"}),HTTP_404_NOT_FOUND

        return  jsonify({"data":{
            "id":bookmark.id,
            "url":bookmark.url,
            "short_url":bookmark.short_url,
            "body":bookmark.body,
            "visits":bookmark.visits,
            "created_at":bookmark.created_at,
            "updated_at":bookmark.updated_at
        },"message":"Bookmark data fetched successfully","status":"success"}),HTTP_200_OK

    except Exception as e:
        return  jsonify({"message":f"Not able to fetch bookmark details: {str(e)}","status":"error"}),HTTP_500_INTERNAL_SERVER_ERROR

@bookmarks.put("/<int:id>")
@bookmarks.patch("/<int:id>")
@jwt_required()
def update_bookmark(id):
    user_id = get_jwt_identity()
    try:
        url = request.json.get("url","")
        body= request.json.get("body","")
        if not validators.url(url):
            return  jsonify({"message":"The URL provided is invalid!!","status":"error"}),HTTP_400_BAD_REQUEST
        bookmark = Bookmark.query.filter_by(user_id=user_id,id=id).first()

        if not bookmark:
            return jsonify({"message": "The bookmark is not found!", "status": "error"}), HTTP_404_NOT_FOUND

        bookmark.url = url
        bookmark.body = body if body else bookmark.body

        db.session.commit()

        return  jsonify({"message":"The bookmark successfully updated!!","status":"success","data":{
            "id":bookmark.id,
            "url":bookmark.url,
            "short_url":bookmark.short_url,
            "body":bookmark.body,
            "visits":bookmark.visits,
            "created_at":bookmark.created_at,
            "updated_at":bookmark.updated_at
        }}),HTTP_200_OK
    except Exception as e:
        return  jsonify({"message":f"Unable to update the bookmark : {str(e)} ","status":"error"})

@bookmarks.delete("/<int:id>")
@jwt_required()
def delete_bookmark(id):
    user_id = get_jwt_identity()

    try:
        bookmark = Bookmark.query.filter_by(user_id=user_id,id=id).first()
        if not bookmark:
            return jsonify({"message":"The bookmark is not found","status":"error"}),HTTP_400_BAD_REQUEST

        db.session.delete(bookmark)
        db.session.commit()
        return jsonify({"message":"The bookmark deleted successfully","status":"success"}),HTTP_204_NO_CONTENT
    except Exception as e:
        return  jsonify({"message":f"Unable to delete the bookmark : {str(e)}","status":"error"}),HTTP_500_INTERNAL_SERVER_ERROR


@bookmarks.get("/stats")
@jwt_required()
def bookmarks_statistics():
    user_id = get_jwt_identity()
    try:
        bookmarks = Bookmark.query.filter_by(user_id=user_id)

        data = [{"id":bm.id,"url":bm.url,"short_url":bm.short_url,"visits":bm.visits} for bm in bookmarks]

        return jsonify({"mesage":"The bookmarks statistics generated successfully","status":"success","data":data})
    except Exception as e:
        return jsonify({"message":f"Something went wrong!, unable to get the bookmarks statistics: {str(e)}","status":"error"}),HTTP_500_INTERNAL_SERVER_ERROR