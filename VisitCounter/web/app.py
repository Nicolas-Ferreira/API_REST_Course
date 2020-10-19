""""

API REQUIREMENTES:
------------------
- Similarity of text
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


# Create our REST API
app = Flask(__name__)
api = Api(app)


# Initialize MongoDB Client
client = MongoClient("mongodb://db:27017") #db as we've defined in the docker-compose file, 27017 default port for MongoDB
db = client.SentencesDataBase #Create a new DB called aNewDB
users = db["Users"] #Create a collection


# Helper functions
def verifyCredentials(username, password):

    hashed_pw = users.find({
        "Username": username
    })[0]["Password"]

    if bcrypt.hashpw(password.encode('utf8'), hashed_pw) == hashed_pw:
        return True
    else:
        return False


def countTokens(username):

    num_tokens = users.find({
        "Username": username
    })[0]["Tokens"]

    return num_tokens



# Define our resources
class Register(Resource):

    def post(self):

        # Get posted data by the user
        postedData = request.get_json()
        username = postedData["username"]
        password = postedData["password"]

        # Hashing password using py-bcrypt
        hashed_pw = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())

        # Store the username and hashed password in the DB
        users.insert({
            "Username": username,
            "Password": hashed_pw,
            "Sentence": "",
            "Tokens": 5
        })

        # Prepare API response
        retJson = {
            "Message": "You successfully signed up for the API",
            "Status Code": 200
        }

        return jsonify(retJson)


class Store(Resource):

    def post(self):

        # Get posted data by the user
        postedData = request.get_json()
        username = postedData["username"]
        password = postedData["password"]
        sentence = postedData["sentence"]

        # Verify Username/Password match
        correct_pw = verifyCredentials(username, password)
        if not correct_pw:
            retJson = {
                "Message": "Incorrect User/Password",
                "Status Code": 302
            }
            return jsonify(retJson)

        # Verify enough tokens
        num_tokens = countTokens(username)
        if num_tokens <= 0:
            retJson = {
                "Message": "Not enough tokens",
                "Status Code": 301
            }
            return jsonify(retJson)

        # Store sentence and return 200 OK
        users.update({
            "Username": username
        }, {
            "$set": {
                "Sentence": sentence,
                "Tokens": num_tokens - 1
            }
        })

        # Prepare API response
        retJson = {
            "Message": "Sentence saved successfully",
            "Status Code": 200
        }
        return jsonify(retJson)


class Get(Resource):

    def post(self):

        # Get posted data by the user
        postedData = request.get_json()
        username = postedData["username"]
        password = postedData["password"]

        # Verify Username/Password match
        correct_pw = verifyCredentials(username, password)
        if not correct_pw:
            retJson = {
                "Message": "Incorrect User/Password",
                "Status Code": 302
            }
            return jsonify(retJson)

        # Verify enough tokens
        num_tokens = countTokens(username)
        if num_tokens <= 0:
            retJson = {
                "Message": "Not enough tokens",
                "Status Code": 301
            }
            return jsonify(retJson)

        # Retreive sentence
        sentence = users.find({
            "Username": username
        })[0]["Sentence"]

        # Reduce 1 token
        users.update({
            "Username": username
        }, {
            "$set": {
                "Tokens": num_tokens - 1
            }
        })

        # Prepare API response
        retJson = {
            "Message": sentence,
            "Status Code": 200
        }
        return jsonify(retJson)


# Add resource to our API
api.add_resource(Register, "/register")
api.add_resource(Store, "/store")
api.add_resource(Get, "/get")


if __name__ == "__main__":
    app.run(host='0.0.0.0')
