from flask import Flask, request
from flask_restful import Api, Resource
import psycopg2
from local_settings import pw

conn = psycopg2.connect(host='pollwatchny.cweqetvzooza.us-west-2.rds.amazonaws.com',dbname='pollwatch',user='pollwatch',password=pw)

app = Flask(__name__)
api = Api(app)

class Address(Resource):
	def get(self):
		streetno = request.args.get('streetno')
		streetname = request.args.get('streetname')
		zipcode = request.args.get('zipcode')
		curs = conn.cursor()
		curs.execute("SELECT ad, ed FROM nyfile WHERE streetno = '%s' AND streetname = '%s' AND zip = '%s'" % (streetno.upper(), streetname.upper(), zipcode))
		conn.commit()
		data = curs.fetchall()
		if len(data) == 0:
			return {'Error' : 'AddressNotFound','streetno' : streetno, 'streetname': streetname, 'zipcode' : zipcode}
		else:
			return {'assembly_district' : data[0][0], 'election_district' : data[0][1]}
		del curs
		
		
api.add_resource(Address,'/')


if __name__ == '__main__':
        app.run()
