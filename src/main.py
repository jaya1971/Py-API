#====================================== Import libraries =========================
import os
import sys
import json
from flask import Flask
from flask import request
import pyodbc
from flask_restful import reqparse, Api, Resource
from dotenv import load_dotenv

#====================================== Initialize Flask =========================
app = Flask(__name__)

#====================================== Setup Flask Restful Framework ============
api = Api(app)
parser = reqparse.RequestParser()
parser.add_argument('query')

#====================================== Setting Up Connection to MSSQL Server ====
load_dotenv()
driver = "Driver={SQL Server}"
drivers = [item for item in pyodbc.drivers()]
driver = drivers[-1]
#print("driver:{}".format(driver))

#====================================== MSSQL Info and Credentials ===============
server = os.getenv('SQLSVR')
database = 'DATABASENAME' 
username = os.getenv('SQLUSER')
password = os.getenv('SQLPW')
con = 'Yes'

if os.getenv('SQLSTRING') == 'prod':
    promostr = 'prodpromo'
elif os.getenv('SQLSTRING') == 'dev':
    promostr = 'promo'

conn = pyodbc.connect(f'DRIVER={driver};Server={server};Database={database};ENCRYPT=no;TrustServerCertificate=yes;UID={username};PWD={password};MARS_Connection={con}')

#====================================== Create Classes ============================
# Promo Class
class Promo(Resource):
    def get(self, promo_number): 
        pl = {"ProjectNumber": promo_number}
        cursor = conn.cursor()   
        try: 
            cursor.execute(f"EXEC  PrizeLogic_ITSurvey.api.get_{promostr} ?", json.dumps(pl))
            result = json.loads(cursor.fetchone()[0])   
        except:
            return "That Promo number doesn't exists!"
            cursor.close()  
        cursor.close()
        return result, 200
        
# Promos Class
class Promos(Resource):
    def get(self):
        cursor = conn.cursor()     
        cursor.execute(f"EXEC PrizeLogic_ITSurvey.api.get_{promostr}s")
        result = json.loads(cursor.fetchone()[0])        
        cursor.close()
        return result, 200

# Employee Class
class Employee(Resource):
    def get(self, employee_id): 
        Eid = {"EmployeeID": employee_id}
        cursor = conn.cursor()   
        try: 
            cursor.execute(f"EXEC  {database}.dbo.getemployee ?", json.dumps(Eid))
            result = json.loads(cursor.fetchone()[0])   
        except:
            return "Employee doesn't exists!"
            cursor.close()  
        cursor.close()
        return result, 200
    
# employees Class
class Employees(Resource):
    def get(self):
        cursor = conn.cursor()     
        cursor.execute(f"EXEC {database}.dbo.getemployees")
        result = json.loads(cursor.fetchone()[0])        
        cursor.close()
        return result, 200
#====================================== Create APIs ============================
api.add_resource(Promos, '/api/promos')
api.add_resource(Promo, '/api/promo/<promo_number>')
api.add_resource(Employees, '/api/employees')
api.add_resource(Employee, '/api/employees/<employee_id>')

#================================Home and health Page ========================================
@app.route('/')
def home():
    return "Welcome to DevOps Python API"

@app.route('/healthy')
def healthy():
    return "Your API is up and running!"

#====================================== Error Handling ==========================
@app.errorhandler(404)
def page_not_found_handler(e):
    return "Invalid route: 404"

@app.errorhandler(401)
def unauthorized_handler(e):
    return "Unauthorized: 401"

@app.errorhandler(403)
def forbidden_handler(e):
    return "Forbidden: 403"

@app.errorhandler(408)
def request_timeout_handler(e):
    return "Request Timeout: 408"

# #====================================== Start App ===============================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 80))
    PORT = 80
    app.run(debug=True, host='0.0.0.0', port=PORT)
