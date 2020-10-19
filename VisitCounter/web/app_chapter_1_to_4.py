from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient


# Create REST API
app = Flask(__name__)
api = Api(app)


# Initialize MongoDB Client
client = MongoClient("mongodb://db:27017") #db as we've defined in the docker-compose file, 27017 default port for MongoDB
db = client.aNewDB #Create a new DB called aNewDB
UserNum = db["UserNum"] #Create a collection
UserNum.insert({
    "num_of_users":0
}) #Insert document



# Define our common functions
def checkPostedData(postedData, functionName):
    if (functionName == "add" or functionName == "subtract" or functionName == "multiply"):
        if "x" not in postedData or "y" not in postedData:
            return 301
        else:
            return 200
    elif (functionName == 'divide'):
        if "x" not in postedData or "y" not in postedData:
            return 301
        elif int(postedData["y"] == 0):
            return 302
        else:
            return 200

# Define our resources
class Visit(Resource):
    # Every time a get request is made on the /visit we will save in the MongoDb the number of users logged in and will return a message with the number
    def get(self):
        prev_num = UserNum.find({})[0]["num_of_users"]
        new_num = prev_num + 1
        UserNum.update({}, {"$set": {"num_of_users": new_num}})
        return str("Hello user " + str(new_num))

class Add(Resource):
    def post(self):
        #If I am here, then the resource Add was requested using the method POST
        # Get the data
        postedData = request.get_json()

        # Verify validity of posted data
        status_code = checkPostedData(postedData, "add")

        # If parameter validation fail return error code
        if (status_code != 200):
            retJson = {
                "Message": "An error happened",
                "Status Code": status_code
            }
            return jsonify(retJson)

        # Calculate de sum
        x = postedData["x"]
        y = postedData["y"]
        x = int(x)
        y = int(y)
        ret = x + y

        # Return results
        retMap = {
            "Message": ret,
            "Status Code": 200
        }
        return jsonify(retMap)

class Subtract(Resource):
    def post(self):
        #If I am here, then the resource Subtract was requested using the method POST
        # Get the data
        postedData = request.get_json()

        # Verify validity of posted data
        status_code = checkPostedData(postedData, "subtract")

        # If parameter validation fail return error code
        if (status_code != 200):
            retJson = {
                "Message": "An error happened",
                "Status Code": status_code
            }
            return jsonify(retJson)

        # Calculate de sum
        x = postedData["x"]
        y = postedData["y"]
        x = int(x)
        y = int(y)
        ret = x - y

        # Return results
        retMap = {
            "Message": ret,
            "Status Code": 200
        }
        return jsonify(retMap)

class Multiply(Resource):
    def post(self):
        #If I am here, then the resource Multiply was requested using the method POST
        # Get the data
        postedData = request.get_json()

        # Verify validity of posted data
        status_code = checkPostedData(postedData, "multiply")

        # If parameter validation fail return error code
        if (status_code != 200):
            retJson = {
                "Message": "An error happened",
                "Status Code": status_code
            }
            return jsonify(retJson)

        # Calculate de sum
        x = postedData["x"]
        y = postedData["y"]
        x = int(x)
        y = int(y)
        ret = x * y

        # Return results
        retMap = {
            "Message": ret,
            "Status Code": 200
        }
        return jsonify(retMap)

class Divide(Resource):
    def post(self):
        #If I am here, then the resource Divide was requested using the method POST
        # Get the data
        postedData = request.get_json()

        # Verify validity of posted data
        status_code = checkPostedData(postedData, "divide")

        # If parameter validation fail return error code
        if (status_code != 200):
            retJson = {
                "Message": "An error happened",
                "Status Code": status_code
            }
            return jsonify(retJson)

        # Calculate de sum
        x = postedData["x"]
        y = postedData["y"]
        x = int(x)
        y = int(y)
        ret = x / y

        # Return results
        retMap = {
            "Message": ret,
            "Status Code": 200
        }
        return jsonify(retMap)

# We need to map the resource to a path, where it will listen
api.add_resource(Add, "/add")
api.add_resource(Subtract, "/sub")
api.add_resource(Multiply, "/mul")
api.add_resource(Divide, "/div")
api.add_resource(Visit, "/visit")


if __name__ == "__main__":
    app.run(host='0.0.0.0')
