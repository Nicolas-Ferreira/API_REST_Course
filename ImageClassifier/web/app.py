""""

API REQUIREMENTS:
-----------------
- Register user
- Classify an image sent by the user
- Refill user tokens


RESOURCE TABLE:
---------------------------------------------------------------------------------------
Resource        Address     Protocol    Parameters              Responses
---------------------------------------------------------------------------------------
Register User   /register   POST        Username: String        200 OK
                                        Password: String        301 Invalid Username
---------------------------------------------------------------------------------------
Classify Image  /classify   POST        Username: String        200 OK
                                        Password: String        301 Invalid Username
                                        Image Url: String       302 Invalid Password
                                                                303 Out of tokens
---------------------------------------------------------------------------------------
Register User   /register   POST        Username: String        200 OK
                                        Admin Password: String  301 Invalid Username
                                        Refill Amount: Integer  304 Invalid Admin Pass
---------------------------------------------------------------------------------------
"""


from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import requests
import subprocess
import json

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")
db = client.ImageRecognition
users = db["Users"]


# Helper Functions
def userExists(username):
    if users.find({"Username": username}).count() == 0:
        return False  # NOT EXISTS
    else:
        return True  # EXISTS

def countTokens(username):
    tokens = users.find({
        "Username": username
    })[0]["Tokens"]
    return tokens

def invalidPassword(username, password):
    # Get Hashed password from the DB
    hashed_pw = users.find({
        "Username": username
    })[0]["Password"]

    # Check if it is the same as the provided
    if bcrypt.hashpw(password.encode("utf8"), hashed_pw) == hashed_pw:
        return False
    else:
        return True

def verifyCredentials(username, password):
    # Check valid username
    if not userExists(username):
        retJson = {
            "Message": "Invalid Username",
            "Status Code": 301
        }
        return retJson, True

    # Check valid password
    if invalidPassword(username, password):
        retJson = {
            "Message": "Invalid Password",
            "Status Code": 302
        }
        return retJson, True

    # Everything is OK
    return None, False

# Resources
class Register(Resource):

    def post(self):

        # Get posted data
        postedData = request.get_json()
        username = postedData["username"]
        password = postedData["password"]

        if userExists(username):
            retJson = {
                "Message": "Invalid Username",
                "Status Code": 301
            }
            return jsonify(retJson)

        hashed_pw = bcrypt.hashpw(password.encode("utf8"), bcrypt.gensalt())
        users.insert({
            "Username": username,
            "Password": hashed_pw,
            "Tokens": 5
        })

        retJson = {
            "Message": "Registered Successfully",
            "Status Code": 200
        }
        return jsonify(retJson)


class Classify(Resource):

    def post(self):

        # Get posted data
        postedData = request.get_json()
        username = postedData["username"]
        password = postedData["password"]
        url = postedData["url"]

        # Validate Username and Password
        retJson, error = verifyCredentials(username, password)
        if error:
            return jsonify(retJson)

        # Verify tokens available
        if countTokens(username) <= 0:
            retJson = {
                "Message": "Out of Tokens",
                "Status Code": 303
            }
            return jsonify(retJson)

        # Get the image from the url and write it to a local file called temp.jpg
        r = requests.get(url)
        retJson = {}
        with open('temp.jpg', 'wb') as f:
            f.write(r.content)
            proc = subprocess.Popen('python classify_image.py --model_dir=. --image_file=./temp.jpg',
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            ret = proc.communicate()[0]
            proc.wait()
            with open("text.txt") as f:
                retJson = json.load(f)

        # Subtract one token
        users.update({
            "Username": username
        }, {
            "$set": {
                "Tokens": countTokens(username) - 1
            }
        })

        return retJson


class Refill(Resource):

    def post(self):

        # Get posted data
        postedData = request.get_json()
        username = postedData["username"]
        admin_password = postedData["admin_pw"]
        amount = postedData["amount"]

        # Check if user exists
        if not userExists(username):
            retJson = {
                "Message": "Invalid Username",
                "Status Code": 301
            }
            return jsonify(retJson)

        # Check Admin password
        correct_admin_pw = "abc123"
        if not admin_password == correct_admin_pw:
            retJson = {
                "Message": "Invalid Admin Password",
                "Status Code": 304
            }
            return jsonify(retJson)

        # Do the refill
        users.update({
            "Username": username
        }, {
            "$set": {
                "Tokens": amount
            }
        })

        retJson = {
            "Message": "Tokens updated correctly",
            "Status Code": 200
        }
        return jsonify(retJson)


api.add_resource(Register, "/register")
api.add_resource(Classify, "/classify")
api.add_resource(Refill, "/refill")

if __name__ == "__main__":
    app.run(host="0.0.0.0")
