import awsgi
from flask import Flask, jsonify, request, make_response
import boto3

app = Flask(__name__)

# Route per ottenere un utente
@app.route("/getUser/<int:userId>", methods=['GET'])
def get_user(userId: int):
    # Prepare the DynamoDB client
    dynamodb = boto3.resource("dynamodb")
    table_name = "users"
    table = dynamodb.Table(table_name)
    # Get the user details from DynamoDB
    db_response = table.get_item(Key={"userId": userId})
    if "Item" in db_response:
        retrieved_first_name = db_response["Item"].get("firstName", "")
        retrieved_last_name = db_response["Item"].get("lastName", "")
        response_body = f"Hello, the user retrieved is {retrieved_first_name} {retrieved_last_name}."
        return make_response(jsonify(response_body), 200, {"Content-Type": "application/json"})        
    else:
        response_body = f"User with userId {{userId}} not found" 
        return make_response(jsonify(response_body), 404, {"Content-Type": "application/json"})

# Route per aggiungere un nuovo utente
@app.route("/addUser", methods=['POST'])
def add_user():
    client_data = request.json
    user_id = client_data.get('userId')
    first_name_to_add = client_data.get('firstName')
    last_name_to_add = client_data.get('lastName')
    # Prepare the DynamoDB client
    dynamodb = boto3.resource("dynamodb")
    table_name = "users"
    table = dynamodb.Table(table_name)
    # Put the new user item into DynamoDB
    db_response = table.put_item(Item={"userId": user_id, "firstName": first_name_to_add, "lastName": last_name_to_add})
    headers = {}
    headers["Content-Type"] = "application/json"
    headers["Access-Control-Allow-Origin"] = "*"
    if db_response['ResponseMetadata']['HTTPStatusCode'] == 200:
        response_body = f"User {first_name_to_add} {last_name_to_add} added successfully"
        status_code = 201
        # return make_response(jsonify(response_body), 201, {"Content-Type": "application/json"})
    else:
        response_body = {"message": "Failed to add user."}
        status_code = 500
        # return make_response(jsonify(response_body), 500, {"Content-Type": "application/json"})
    return make_response(jsonify(response_body), status_code, headers)

def lambda_handler(event, context):
    return awsgi.response(app, event, context)
