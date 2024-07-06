import awsgi
from flask import Flask, jsonify, request, make_response
import boto3

app = Flask(__name__)

# Costanti per i nomi delle tabelle e dei campi
USERS_TABLE_NAME = "users"
USER_ID_FIELD = "userId"
FIRST_NAME_FIELD = "firstName"
LAST_NAME_FIELD = "lastName"
COUNTERS_TABLE_NAME = "id_counters"
TABLE_NAME_FIELD = "table_name"
COUNTER_VALUE_FIELD = "counter_value"
AWS_DB_SERVICE_NAME = "dynamodb"
APPL_JSON_HEADER = "application/json"
STAR_VALUE = "*"
CONTENT_TYPE = "Content-Type"
ACCESS_CONTROL_ALLOW_ORIGIN = "Access-Control-Allow-Origin"
UPDATED_NEW = "UPDATED_NEW"

# Lo scopo del seguente codice e' la definizione della classe User per usare i metodi get/add in modo da lasciare gli endpoinit delle FLASK API più leggibili  
class UserService:
    def __init__(self):
        # Connessione a DB mediante costruttore User (mediante ResourceObject)
        self.dynamodb = boto3.resource(AWS_DB_SERVICE_NAME)
        self.users_table = self.dynamodb.Table(USERS_TABLE_NAME)
        self.counters_table = self.dynamodb.Table(COUNTERS_TABLE_NAME)
        
    def get_user_from_db(self, userId: int):
        # Recupera Info utente da DynamoDB accedendo alla risposta in forma di dizionario
        try:
            db_response = self.users_table.get_item(Key={USER_ID_FIELD: userId})
            if "Item" in db_response:
                retrieved_first_name = db_response["Item"].get(FIRST_NAME_FIELD, "")
                retrieved_last_name = db_response["Item"].get(LAST_NAME_FIELD, "")
                response_body = f"Hello, the user retrieved is {retrieved_first_name} {retrieved_last_name}."
                return make_response(jsonify(response_body), 200, {CONTENT_TYPE: APPL_JSON_HEADER})
            else:
                response_body = f"User with userId {userId} not found"
                return make_response(jsonify({"message": response_body}), 404, {CONTENT_TYPE: APPL_JSON_HEADER})
        except Exception as e:
            return make_response(jsonify({"message": str(e)}), 500, {CONTENT_TYPE: APPL_JSON_HEADER})
        
    def add_user_to_db(self):
        client_data = request.json
        first_name_to_add = client_data.get(FIRST_NAME_FIELD)
        last_name_to_add = client_data.get(LAST_NAME_FIELD)
        # Validazione INPUT prima di slavare a DB
        if not first_name_to_add or not last_name_to_add:
            return make_response(jsonify({"message": "First name and last name are required"}), 400, {CONTENT_TYPE: APPL_JSON_HEADER})

        try:
            # Gestione dell'autoincrement sulle primary key in fase di salvataggio utente
            user_id = self.get_next_id(USERS_TABLE_NAME)
            # Salva utente a DB e memorizza la risposta del Database in una variabile db_response
            db_response = self.users_table.put_item(Item={USER_ID_FIELD: user_id, FIRST_NAME_FIELD: first_name_to_add, LAST_NAME_FIELD: last_name_to_add})
            headers = {
                CONTENT_TYPE: APPL_JSON_HEADER,
                ACCESS_CONTROL_ALLOW_ORIGIN: STAR_VALUE
            }
            if db_response['ResponseMetadata']['HTTPStatusCode'] == 200:
                response_body = f"User {first_name_to_add} {last_name_to_add} added successfully"
                status_code = 201
            else:
                response_body = {"message": "Failed to add user."}
                status_code = 500
            return make_response(jsonify(response_body), status_code, headers)
        except Exception as e:
            return make_response(jsonify({"message": str(e)}), 500, {CONTENT_TYPE: APPL_JSON_HEADER})
    
    def get_next_id(self, table_name: str):
        try:
            response = self.counters_table.update_item(
                Key={TABLE_NAME_FIELD: table_name},
                UpdateExpression="SET " + COUNTER_VALUE_FIELD + " = " + COUNTER_VALUE_FIELD + " + :increment",
                ExpressionAttributeValues={":increment": 1},
                # restituisce il contatore aggiornato delle nuple presenti per quella specifica tabella  (in questo caso table_name = 'user')
                ReturnValues=UPDATED_NEW
            )
            return response["Attributes"][COUNTER_VALUE_FIELD]
        except Exception as e:
            raise Exception(f"Failed to get next ID: {str(e)}")

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