from game import models
import random

# Cities amount equals brokers amount
def city_generator(brokers_amount):
	cities = [
		'IV',
		'WS',
		'TT',
		'AD',
		'NF',
		'ET',
	]
	cities_for_iter = cities[:brokers_amount]
	while True:
		yield cities_for_iter.pop(random.randint(0, len(cities_for_iter) - 1))
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
	producer_players = session_instance.player.filter(role='producer')
	broker_players = session_instance.player.filter(role='broker')
	city = city_generator(session_instance.number_of_brokers)
	name_gen = name_generator()
	number_of_brokers = session_instance.number_of_brokers
	for broker_player in broker_players:
		broker_player.city = next(city)
		broker_player.map_url = f"/static/{number_of_brokers}_brokers/map.jpg"
		broker_player.balance = session_instance.broker_starting_balance
		broker_player.logistics_url = f"/static/broker" \
									  f"/{city_names[broker_player.city]}.png"
		broker_player.role_name = city_broker_names[broker_player.city]
		broker_player.save()
		models.BrokerModel.objects.create(player=broker_player).save()

	for producer_player in producer_players:
		producer_player.city = next(city)
		producer_player.map_url = f"/static/{number_of_brokers}_brokers/map.jpg"
		producer_player.balance = session_instance.producer_starting_balance
		producer_player\
			.logistics_url = f"/static/{number_of_brokers}_broker/producer/" \
							 f"{city_names[producer_player.city]}.png"
		producer_player.role_name = next(name_gen)
		producer_player.save()
		models.ProducerModel.objects.create(player=producer_player).save()
