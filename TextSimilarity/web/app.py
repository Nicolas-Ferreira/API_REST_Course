""""

API REQUIREMENTES:
------------------
- Similarity of text using a pre-trained spacy model (en_core_web_sm)
- Will receive two documents and return how similarity are
- Each user will have a limited number of tokens
- There should be the chance to refill so we need an endpoint to do this

RESOURCE TABLE:
---------------------------------------------------------------------------------------
Resource        Address     Protocol    Parameters          Responses
---------------------------------------------------------------------------------------
Register User   /register   POST        User: String        200 OK
                                        Pass: String        301 Username taken
---------------------------------------------------------------------------------------
Detect          /detect     POST        User: String        200 OK
Similarity                              Pass: String        301 Invalid username
of Documents                            Text1: String       302 Invalid ps
                                        Text2: String       303 Out of tokens
---------------------------------------------------------------------------------------
Refill          /refill     POST        User: String        200 OK
                                        AdminPass: String   301 Invalid username
                                        Refill amount: Int  304 Invalid Admin password
---------------------------------------------------------------------------------------
"""

from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import spacy


# Construct our App
app = Flask(__name__)
api = Api(app)


# Connecto to MongoDB, create new DB and new collection
client = MongoClient("mongodb://db.27017")
db = client.SimilarityDB
users = db["Users"]


# Helper funtions
def userExists(username):
    # If the user exists in the DB I'll return True
    if users.find({"Username": username}).count() == 0:
        return False
    else:
        return True

def invalidPassword(username, password):

    if not userExists(username):
        return False

    # Get Hashed password from the DB
    hashed_pw = users.find({
        "Username": username
    })[0]["Password"]

    # Check if it is the same as the provided
    if bcrypt.hashpw(password.encode("utf8"), hashed_pw) == hashed_pw:
        return True
    else:
        return False

def countTokens(username):

    num_tokens = users.find({
        "Username": username
    })[0]["Tokens"]
    return num_tokens


# Implement our resources
class Register(Resource):

    def post(self):

        # Get request data
        postedData = request.get_json()
        username = postedData["username"]
        password = postedData["password"]

        # Check if the username already exists
        if userExists(username):
            retJson = {
                "Message": "Username already taken",
                "Status Code": 301
            }
            return jsonify(retJson)

        # Hash password to store in the DB
        hashed_pw = bcrypt.hashpw(password.encode("utf8"), bcrypt.gensalt())

        # Insert user and password into the DB
        users.insert({
            "Username": username,
            "Password": hashed_pw,
            "Tokens": 6
        })

        # Return 200 OK
        retJson = {
            "Message": "You've successfully signed up to the API",
            "Status Code": 200
        }

        return jsonify(retJson)


class Detect(Resource):

    def post(self):

        # Get request data
        postedData = request.get_json()
        username = postedData["username"]
        password = postedData["password"]
        text1 = postedData["text1"]
        text2 = postedData["text2"]

        # Check valid username
        if userExists(username):
            retJson = {
                "Message": "Invalid Username",
                "Status Code": 301
            }
            return jsonify(retJson)

        # Check valid password
        if invalidPassword(username, password):
            retJson = {
                "Message": "Invalid Password",
                "Status Code": 302
            }
            return jsonify(retJson)

        # Check if the user has available tokens
        if countTokens(username) <= 0:
            retJson = {
                "Message": "Out of Tokens",
                "Status Code": 303
            }
            return jsonify(retJson)

        # Calculate the texts similarity
        nlp = spacy.load("en_core_web_sm")
        text1 = nlp(text1)
        text2 = nlp(text2)

        # Ratio is a number between 0 and 1, the closer to 1 the more similar text1 and text2 are
        ratio = text1.similarity(text2)

        # Subtract one token from the user count
        current_tokens = countTokens(username) - 1
        users.update({
            "Username": username
        }, {
            "$set": {
                "Tokens": current_tokens
            }
        })

        # Return 200 OK
        retJson = {
            "Message": "Similarity calculated",
            "Similarity": ratio,
            "Status Code": 200
        }

        return jsonify(retJson)


class Refill(Resource):

    def post(self):

        # Get request data
        postedData = request.get_json()
        username = postedData["username"]
        adminpass = postedData["admin_pw"]
        refill_amount = postedData["refill"]

        # Check valid username
        if userExists(username):
            retJson = {
                "Message": "Invalid Username",
                "Status Code": 301
            }
            return jsonify(retJson)

        # Check valid admin password
        correct_pw = "abc123" # This was just for educational purposes
        if adminpass != correct_pw:
            retJson = {
                "Message": "Invalid Admin Password",
                "Status Code": 304
            }
            return jsonify(retJson)

        # Update the tokens
        users.update({
            "Username": username
        }, {
            "$set": {
                "Tokens": refill_amount
            }
        })

        # Return 200 OK
        retJson = {
            "Message": "Refilled Successfully",
            "Status Code": 200
        }

        return jsonify(retJson)


# Create endpoints for each Resource
api.add_resource(Register, "/register")
api.add_resource(Detect, "/detect")
api.add_resource(Refill, "/refill")


if __name__ == "__main__":
    app.run(host="0.0.0.0")

