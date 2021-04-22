from game import models
import random


def city_generator(players_amount, brokers_amount):
	cities = [
		'IV',
		'WS',
		'TT',
		'AD',
		'NF',
		'ET',
	]
	cities_for_iter = cities[:brokers_amount]
	while players_amount > 0:
		yield cities_for_iter.pop(random.randint(0, len(cities_for_iter) - 1))
		players_amount -= 1
		if len(cities_for_iter) == 0:
			cities_for_iter = cities[:brokers_amount]


def name_generator():
	names = [
		"Арнольд",
		"Антэйн",
		"Артур",
		"Бернард",
		"Беррак",
		"Брэйди",
		"Вильям",
		"Генрих",
		"Геральд",
		"Густав",
		"Двэйн",
		"Донован",
		"Жак",
		"Карл",
		"Кевин",
		"Конан",
		"Летард",
		"Леонард",
		"Людвиг",
		"Малоун",
		"Модест",
		"Мерфи",
		"Отто",
		"Оскар",
		"Риган",
		"Ричард",
		"Роберт",
		"Ролан",
		"Уиллиам",
		"Фалько",
		"Фицрой",
		"Харбин",
		"Эдгар",
		"Эдмунд",
		"Эраст",
		"Эдвард",
	]
	random.shuffle(names)
	for name in names:
		yield name


city_names = {
	'IV': 'ivo',
	'WS': 'wemshire',
	'TT': 'tortuga',
	'AD': 'alendor',
	'NF': 'neverfall',
	'ET': 'etrua',
}

city_broker_names = {
	'IV': 'Мр. Смит',
	'WS': 'Мр. Ли',
	'TT': 'Мр. Джонсон',
	'AD': 'Мр. Майклсон',
	'NF': 'Мр. Эриксон',
	'ET': 'Мр. Робертс',
}


def generate_role_instances(session_instance):
	players = session_instance.player.all()
	city = city_generator(players.count(), session_instance.number_of_brokers)
	name_gen = name_generator()
	number_of_brokers = session_instance.number_of_brokers
	for player in players:
		player.city = next(city)
		player.map_url = f"/static/{number_of_brokers}_brokers/map.jpg"
		if player.role == 'producer':
			player.balance = session_instance.producer_starting_balance
			player.logistics_url = f"/static/{number_of_brokers}_brokers/producer/{city_names[player.city]}.png"
			player.role_name = next(name_gen)
			player.save()
			models.ProducerModel.objects.create(player=player).save()
		else:
			player.balance = session_instance.broker_starting_balance
			player.logistics_url = f"/static/broker/{city_names[player.city]}.png"
			player.role_name = city_broker_names[player.city]
			player.save()
			models.BrokerModel.objects.create(player=player).save()
