from pyramid.view import view_config, view_defaults
from pyramid.response import Response
from ..models import DatabaseInterface
import json


@view_defaults(renderer='json')
class Users:
	def __init__(self, request):
		self.request = request
		self.DB = DatabaseInterface(self.request.dbsession)

	@view_config(route_name='configurations', request_method="OPTIONS")
	def configurations_OPTIONS(self):
		res = Response()
		res.headers.add('Access-Control-Allow-Origin', '*')
		res.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
		res.headers.add('Access-Control-Allow-Headers', 'username')
		return res

	#5 List configurations for specific user
	@view_config(route_name='configurations', request_method="GET")
	def configurations_GET(self):
	#Also adds the user to the DB if it doesn't exist
		username = self.request.headers.get('username')
		user = self.DB.checkUser(username)
		self.DB.assignUserToExperiments(user.id)
		confs = self.DB.getConfigurationForUser(user.id)
		configurations = []
		for conf in confs:
			configurations.append({'key':conf.key, 'value':conf.value})
		output = json.dumps({'data': configurations})
		headers = ()
		res = Response(output)
		res.headers.add('Access-Control-Allow-Origin', '*')
		return res

	@view_config(route_name='users', request_method="OPTIONS")
	def users_OPTIONS(self):
		res = Response()
		res.headers.add('Access-Control-Allow-Origin', '*')
		res.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
		return res

	#6 List all users
	@view_config(route_name='users', request_method="GET")
	def users_GET(self):
		users = self.DB.getAllUsers()
		usersJSON = []
		for i in range(len(users)):
			user = {
			'id':users[i].id, 
			'username':users[i].username, 
			'totalDataitems':self.DB.getTotalDataitemsForUser(users[i].id)}
			usersJSON.append(user)
		output = json.dumps({'data': usersJSON})
		headers = ()
		res = Response(output)
		res.headers.add('Access-Control-Allow-Origin', '*')
		return res

	@view_config(route_name='experiments_for_user', request_method="OPTIONS")
	def experiments_for_user_OPTIONS(self):
		res = Response()
		res.headers.add('Access-Control-Allow-Origin', '*')
		res.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
		return res

	#8 List all experiments for specific user 
	@view_config(route_name='experiments_for_user', request_method="GET")
	def experiments_for_user_GET(self):
		id = int(self.request.matchdict['id'])
		experiments = self.DB.getExperimentsUserParticipates(id)
		experimentsJSON = []
		for i in range(len(experiments)):
			experimentgroup = self.DB.getExperimentgroupForUserInExperiment(id, experiments[i].id)
			expgroup = {'id': experimentgroup.id, 'name':experimentgroup.name}
			exp = {'id':experiments[i].id, 'name': experiments[i].name, 'experimentgroup': expgroup}
			experimentsJSON.append(exp)
		output = json.dumps({'data': experimentsJSON})
		headers = ()
		res = Response(output)
		res.headers.add('Access-Control-Allow-Origin', '*')
		return res

	@view_config(route_name='events', request_method="OPTIONS")
	def events_OPTIONS(self):
		res = Response()
		res.headers.add('Access-Control-Allow-Origin', '*')
		res.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
		res.headers.add('Access-Control-Allow-Headers', 'username')
		return res

	#9 Save experiment data
	@view_config(route_name='events', request_method="POST")
	def events_POST(self):
		json = self.request.json_body
		value = json['value']
		key = json['key']
		username = self.request.headers['username']
		user = self.DB.getUserByUsername(username)
		self.DB.createDataitem({'user': user.id, 'value': value, 'key':key})

	@view_config(route_name='user', request_method="OPTIONS")
	def user_OPTIONS(self):
		res = Response()
		res.headers.add('Access-Control-Allow-Origin', '*')
		res.headers.add('Access-Control-Allow-Methods', 'DELETE,OPTIONS')
		return res

	#10 Delete user
	@view_config(route_name='user', request_method="DELETE")
	def user_DELETE(self):
		self.DB.deleteUser(self.request.matchdict['id'])












	