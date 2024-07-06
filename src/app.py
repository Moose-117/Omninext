import awsgi
from flask import Flask, jsonify, request, make_response
import boto3

app = Flask(__name__)

# Costanti per i nomi delle tabelle e dei campi

USERS_TABLE_NAME = "users"
USER_ID_FIELD = "userId"
FIRST_NAME_FIELD = "firstName"
LAST_NAME_FIELD = "lastName"
AWS_DB_SERVICE_NAME = "dynamodb"
APPL_JSON_HEADER = "application/json"
STAR_VALUE = "*"
CONTENT_TYPE ="Content-Type"
ACCESS_CONTROL_ALLOW_ORIGIN = "Access-Control-Allow-Origin"

class UserService():
        
    def __init__(self):
        # Prepare the DynamoDB client
        self.dynamodb = boto3.resource(AWS_DB_SERVICE_NAME)
        self.table_name = USERS_TABLE_NAME
        self.table = self.dynamodb.Table(self.table_name)
        
    def get_user_from_db(self, userId: int):
        # Get the user details from DynamoDB
        db_response = self.table.get_item(Key={"userId": userId})
        if "Item" in db_response:
            retrieved_first_name = db_response["Item"].get(FIRST_NAME_FIELD, "")
            retrieved_last_name = db_response["Item"].get(LAST_NAME_FIELD, "")
            response_body = f"Hello, the user retrieved is {retrieved_first_name} {retrieved_last_name}."
            return make_response(jsonify(response_body), 200, {CONTENT_TYPE: APPL_JSON_HEADER})        
        else:
            response_body = f"User with userId {userId} not found" 
            return make_response(jsonify(response_body), 404, {CONTENT_TYPE: APPL_JSON_HEADER})
        
    def add_user_to_db(self):
        client_data = request.json
        user_id = client_data.get(USER_ID_FIELD)
        first_name_to_add = client_data.get(FIRST_NAME_FIELD)
        last_name_to_add = client_data.get(LAST_NAME_FIELD)
        
        # Put the new user item into DynamoDB
        db_response = self.table.put_item(Item={USER_ID_FIELD: user_id, FIRST_NAME_FIELD: first_name_to_add, LAST_NAME_FIELD: last_name_to_add})
        headers = {}
        headers[CONTENT_TYPE] = APPL_JSON_HEADER
        headers[ACCESS_CONTROL_ALLOW_ORIGIN] = STAR_VALUE
        if db_response['ResponseMetadata']['HTTPStatusCode'] == 200:
            response_body = f"User {first_name_to_add} {last_name_to_add} added successfully"
            status_code = 201
        else:
            response_body = {"message": "Failed to add user."}
            status_code = 500
        return make_response(jsonify(response_body), status_code, headers)

# Creazione di un'istanza della classe UserService
userService = UserService()

# Route per ottenere un utente
@app.route("/getUser/<int:userId>", methods=['GET'])
def get_user(userId: int):
    return userService.get_user_from_db(userId)

# Route per aggiungere un nuovo utente
@app.route("/addUser", methods=['POST'])
def add_user():
    return userService.add_user_to_db()
    
def lambda_handler(event, context):
    return awsgi.response(app, event, context)
