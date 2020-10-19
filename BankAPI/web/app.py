"""

API REQUIREMENTS:
-----------------
- Open accounts
- Add money to the account
- Transfer money to another account
- Request a loan

RESOURCE TABLE:
------------------------------------------------------------------------------------------------
Resource            Address         Protocol    Parameters                  Responses
------------------------------------------------------------------------------------------------
Register            /register       POST        Username: String            200 OK
                                                Password: String            301 Invalid Username
------------------------------------------------------------------------------------------------
Add money           /add            POST        Username: String            200 OK
                                                Password: String            301 Invalid Username
                                                Amount: Float               302 Invalid Password
                                                                            304 Invalid Amount
------------------------------------------------------------------------------------------------
Transfer            /transfer       POST        Username: String            200 OK
                                                Password: String            301 Invalid Username
                                                To Username: String         302 Invalid Password
                                                Amount: Float               303 Not Enough Money
                                                                            304 Invalid Amount
------------------------------------------------------------------------------------------------
Check Balance       /balance        POST        Username: String            200 OK
                                                Password: String            301 Invalid Username
                                                                            302 Invalid Password
------------------------------------------------------------------------------------------------
Take Loan           /take_loan      POST        Username: String            200 OK
                                                Password: String            301 Invalid Username
                                                Amount: Float               302 Invalid Password
                                                                            304 Invalid Amount
------------------------------------------------------------------------------------------------
Pay Loan            /pay_loan       POST        Username: String            200 OK
                                                Password: String            303 Not Enough Money
                                                Amount: Float               304 Invalid Amount
------------------------------------------------------------------------------------------------
"""

from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt


# Initialize API
app = Flask(__name__)
api = Api(app)


# Initialize MongoDB
client = MongoClient()
db = client.BankDB
alertas = db["alertas"]


# Helper functions
def userExists(username):
    if users.find({"Username": username}).count() == 0:
        return False
    else:
        return True

def verifyPassword(username, password):
    if not userExists(username):
        return False

    hashed_pw = users.find({
        "Username": username
    })[0]["Password"]

    if bcrypt.hashpw(password.encode("utf8"), hashed_pw) == hashed_pw:
        return True
    else:
        return False

def getBalance(username):
    amount = users.find({
        "Username": username
    })[0]["Own"]
    return amount

def getDebt(username):
    amount = users.find({
        "Username": username
    })[0]["Debt"]
    return amount

def generateReturnDict(message, status_code):
    retJson = {
        "Message": message,
        "Status Code": status_code
    }
    return retJson

def verifyCredentials(username, password):
    if not userExists(username):
        return generateReturnDict("Invalid Username", 301), True
    correct_pw = verifyPassword(username, password)
    if not correct_pw:
        return generateReturnDict("Invalid Password", 302), True
    return None, False

def setBalance(username, amount):
    users.update({
        "Username": username
    }, {
        "$set": {
            "Own": amount
        }
    })

def setDebt(username, amount):
    users.update({
        "Username": username
    }, {
        "$set": {
            "Debt": amount
        }
    })


# Resources
class Register(Resource):

    def post(self):

        # Get posted data
        postedData = request.get_json()
        username = postedData["username"]
        password = postedData["password"]

        # Verify user exists
        if userExists(username):
            retJson = generateReturnDict("Invalid Username", 301)
            return jsonify(retJson)

        hashed_pw = bcrypt.hashpw(password.encode("utf8"), bcrypt.gensalt())
        users.insert({
            "Username": username,
            "Password": hashed_pw,
            "Own": 0,
            "Debt": 0
        })
        retJson = generateReturnDict("Registered Successfully", 200)
        return jsonify(retJson)

class Add(Resource):

    def post(self):

        # Get posted data
        postedData = request.get_json()
        username = postedData["username"]
        password = postedData["password"]
        amount = postedData["amount"]

        # Verify the credentials
        retJson, error = verifyCredentials(username, password)
        if error:
            return jsonify(retJson)

        # Check amount
        if amount <= 0:
            return jsonify(generateReturnDict("Invalid Amount", 304))

        # Take fee and update BANK BALANCE
        amount -= 1  # Charge Fee
        bank_cash = getBalance("BANK")  # BANK balance
        setBalance("BANK", bank_cash + 1)  # Update BANK balance

        # Update User balance
        cash = getBalance(username)
        setBalance(username, cash + amount)

        return jsonify(generateReturnDict("Amount added successfully to your account", 200))

class Transfer(Resource):

    def post(self):

        # Get posted data
        postedData = request.get_json()
        username = postedData["username"]
        password = postedData["password"]
        to_username = postedData["to"]
        amount = postedData["amount"]

        # Verify credentials
        retJson, error = verifyCredentials(username, password)
        if error:
            return jsonify(retJson)

        # Check amount
        if amount <= 0:
            return jsonify(generateReturnDict("Invalid Amount", 304))

        # Verify if user has mone to transfer
        cash = getBalance(username)
        if cash < amount:
            return jsonify(generateReturnDict("Not Enough Money", 303))

        # Verify to_username exists
        if not userExists(to_username):
            return jsonify(generateReturnDict("Invalid Receiver username", 301))

        cash_from = getBalance(username)
        cash_to = getBalance(to_username)
        cash_bank = getBalance("BANK")

        setBalance("BANK", cash_bank + 1)  # Transaction Fee
        setBalance(to_username, cash_to + amount - 1)
        setBalance(username, cash_from - amount)

        return jsonify(generateReturnDict("Transaction Completed", 200))

class Balance(Resource):

    def post(self):

        # Get posted data
        postedData = request.get_json()
        username = postedData["username"]
        password = postedData["password"]

        # Verify credentials
        retJson, error = verifyCredentials(username, password)
        if error:
            return jsonify(retJson)

        cash = getBalance(username)
        debt = getDebt(username)
        return jsonify(generateReturnDict("Balance: " + str(cash) + " / Debt: " + str(debt), 200))

class TakeLoan(Resource):

    def post(self):

        # Get posted data
        postedData = request.get_json()
        username = postedData["username"]
        password = postedData["password"]
        amount = postedData["amount"]

        # Verify Credentials
        retJson, error = verifyCredentials(username, password)
        if error:
            return jsonify(retJson)

        # Check amount
        if amount <= 0:
            return jsonify(generateReturnDict("Invalid Amount", 304))

        cash = getBalance(username)
        debt = getDebt(username)
        setBalance(username, cash + amount)
        setDebt(username, debt + amount)

        return jsonify(generateReturnDict("Loan added to your account", 200))

class PayLoan(Resource):

    def post(self):

        # Get posted data
        postedData = request.get_json()
        username = postedData["username"]
        password = postedData["password"]
        amount = postedData["amount"]

        # Verify Credentials
        retJson, error = verifyCredentials(username, password)
        if error:
            return jsonify(retJson)

        # Check amount
        if amount <= 0:
            return jsonify(generateReturnDict("Invalid Amount", 304))

        cash = getBalance(username)
        if cash < amount:
            return jsonify(generateReturnDict("Not enough money", 303))

        debt = getDebt(username)
        setBalance(username, cash - amount)
        setDebt(username, debt - amount)

        return jsonify(generateReturnDict("Loan paid successfully", 200))


# Add resources to our API
api.add_resource(Register, "/register")
api.add_resource(Add, "/add")
api.add_resource(Transfer, "/transfer")
api.add_resource(Balance, "/balance")
api.add_resource(TakeLoan, "/take_loan")
api.add_resource(PayLoan, "/pay_loan")

if __name__ == "__main__":
    app.run(host="0.0.0.0")
