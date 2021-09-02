# logistic constants
cost_for_length = {
	'green': 10,
	'yellow': 15,
	'red': 20,
}

# call: transporting_cost[brokers_amount][city_from][city_to]
transporting_cost = {
	3: {
		'IV': {
			'IV': cost_for_length['green'],
			'WS': cost_for_length['yellow'],
			'TT': cost_for_length['red'],
		},
		'WS': {
			'IV': cost_for_length['red'],
			'WS': cost_for_length['green'],
			'TT': cost_for_length['yellow'],
		},
		'TT': {
			'IV': cost_for_length['red'],
			'WS': cost_for_length['yellow'],
			'TT': cost_for_length['green'],
		},
	},
	4: {
		'IV': {
			'IV': cost_for_length['green'],
			'WS': cost_for_length['yellow'],
			'TT': cost_for_length['red'],
			'AD': cost_for_length['yellow'],
		},
		'WS': {
			'IV': cost_for_length['yellow'],
			'WS': cost_for_length['green'],
			'TT': cost_for_length['yellow'],
			'AD': cost_for_length['red'],
		},
		'TT': {
			'IV': cost_for_length['red'],
			'WS': cost_for_length['yellow'],
			'TT': cost_for_length['green'],
			'AD': cost_for_length['yellow'],
		},
		'AD': {
			'IV': cost_for_length['yellow'],
			'WS': cost_for_length['red'],
			'TT': cost_for_length['yellow'],
			'AD': cost_for_length['green'],
		},
	},
	5: {
		'IV': {
			'IV': cost_for_length['green'],
			'WS': cost_for_length['yellow'],
			'TT': cost_for_length['red'],
			'AD': cost_for_length['yellow'],
			'NF': cost_for_length['red'],
		},
		'WS': {
			'IV': cost_for_length['yellow'],
			'WS': cost_for_length['green'],
			'TT': cost_for_length['yellow'],
			'AD': cost_for_length['red'],
			'NF': cost_for_length['red'],
		},
		'TT': {
			'IV': cost_for_length['red'],
			'WS': cost_for_length['yellow'],
			'TT': cost_for_length['green'],
			'AD': cost_for_length['red'],
			'NF': cost_for_length['yellow'],
		},
		'AD': {
			'IV': cost_for_length['yellow'],
			'WS': cost_for_length['red'],
			'TT': cost_for_length['red'],
			'AD': cost_for_length['green'],
			'NF': cost_for_length['yellow'],
		},
		'NF': {
			'IV': cost_for_length['red'],
			'WS': cost_for_length['red'],
			'TT': cost_for_length['yellow'],
			'AD': cost_for_length['yellow'],
			'NF': cost_for_length['green'],
		},
	},
	6: {
		'IV': {
			'IV': cost_for_length['green'],
			'WS': cost_for_length['yellow'],
			'TT': cost_for_length['red'],
			'AD': cost_for_length['yellow'],
			'NF': cost_for_length['red'],
			'ET': cost_for_length['red'],
		},
		'WS': {
			'IV': cost_for_length['yellow'],
			'WS': cost_for_length['green'],
			'TT': cost_for_length['yellow'],
			'AD': cost_for_length['red'],
			'NF': cost_for_length['red'],
			'ET': cost_for_length['red'],
		},
		'TT': {
			'IV': cost_for_length['red'],
			'WS': cost_for_length['yellow'],
			'TT': cost_for_length['green'],
			'AD': cost_for_length['red'],
			'NF': cost_for_length['yellow'],
			'ET': cost_for_length['red'],
		},
		'AD': {
			'IV': cost_for_length['yellow'],
			'WS': cost_for_length['red'],
			'TT': cost_for_length['red'],
			'AD': cost_for_length['green'],
			'NF': cost_for_length['red'],
			'ET': cost_for_length['yellow'],
		},
		'NF': {
			'IV': cost_for_length['red'],
			'WS': cost_for_length['red'],
			'TT': cost_for_length['yellow'],
			'AD': cost_for_length['red'],
			'NF': cost_for_length['yellow'],
			'ET': cost_for_length['green'],
		},
		'ET': {
			'IV': cost_for_length['red'],
			'WS': cost_for_length['red'],
			'TT': cost_for_length['red'],
			'AD': cost_for_length['yellow'],
			'NF': cost_for_length['yellow'],
			'ET': cost_for_length['green'],
		},
	},
}


def get_transporting_cost(brokers_count, broker_city, producer_city):
	cities = ['IV', 'WS', 'TT', 'AD', 'NF', 'ET']
	if brokers_count < 3 or brokers_count > 6:
		raise Exception('Invalid brokers amount!')
	elif broker_city not in cities or producer_city not in cities:
		raise Exception('Invalid city!')
	try:
		return transporting_cost[brokers_count][producer_city][broker_city]
	except KeyError:
		raise Exception('Wrong city!')
