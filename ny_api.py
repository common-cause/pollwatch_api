from flask import Flask, request
from flask_restful import Api, Resource
import psycopg2
from local_settings import pw
import requests
import json
import re

conn = psycopg2.connect(host='pollwatchny.cweqetvzooza.us-west-2.rds.amazonaws.com',dbname='pollwatch',user='pollwatch',password=pw)

app = Flask(__name__)
api = Api(app)

class AddressError(Exception):
	def __init__(self):
		pass
		
directions = {'E' : 'EAST', 'W' : 'WEST', 'S' : 'SOUTH', 'N' : 'NORTH'}
types = {'ST' : 'STREET', 'STREET' : 'STREET', 'AVE' : 'AVENUE', 'AVENUE' : 'AVENUE'}

def nyc_lookup(streetno, streetname, zipcode,attempt=1):
	endpoint = 'http://nyc.electionapi.com/psl/pollsiteinfo'
	payload = {'key' : '979e41df-0bf3-4ae4-97d7-16da76f6af65', 'streetnumber' : streetno, 'streetname' : streetname, 'postalcode' : zipcode}
	api_data = json.loads(requests.get(endpoint,params=payload).text)
	try:
		ed_data = api_data['election_district'].split('/')
		return {'assembly_district' : ed_data[1], 'election_district' : ed_data[0]}
	except KeyError:
		if attempt < 6:
			return nyc_lookup(streetno, streetname, zipcode, attempt=attempt+1)
		raise AddressError

def upstate_lookup(streetno, streetname, zipcode,attempts=0):
	curs = conn.cursor()
	curs.execute("SELECT ad, ed FROM nyfile WHERE streetno = '%s' AND (streetname = '%s' OR streetname = replace('%s','TRAIL','TRL')) AND zip = '%s'" % (streetno.upper(), streetname.upper(), streetname.upper(), zipcode))
	conn.commit()
	data = curs.fetchall()
	if len(data) == 0 and attempts == 0:
		if re.match(re.compile('[SNEW] \d+'), streetname.upper()) is not None:
			comps = streetname.upper().split(' ')
			newaddress =  directions[comps[0]]+ ' ' + re.match(re.compile('(\d+)'),comps[1]).groups(0)[0] + ' ' + types[comps[-1]]
			return upstate_lookup(streetno,newaddress,zipcode,attempts=1)
		raise AddressError
	else:
		del curs
		return {'assembly_district' : data[0][0], 'election_district' : data[0][1]}

class Address(Resource):
	def get(self):
		streetno = request.args.get('streetno')
		streetname = request.args.get('streetname')
		zipcode = request.args.get('zipcode')
		county = request.args.get('county')
		try:
			#if county in ['Kings County','New York County','Richmond County','Queens County','Bronx County']:
			#	return nyc_lookup(streetno, streetname, zipcode)
			#else:
			return upstate_lookup(streetno, streetname, zipcode)
		except AddressError:
			return {'Error' : 'AddressNotFound','streetno' : streetno, 'streetname': streetname, 'zipcode' : zipcode}
	
		
api.add_resource(Address,'/')


if __name__ == '__main__':
        app.run()

		
