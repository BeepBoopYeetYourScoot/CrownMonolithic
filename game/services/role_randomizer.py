import random


def distribute_roles(session_instance):
	"""
	Распределяет роли игроков в сессии
	"""
	players_queryset = session_instance.player.all()
	print(players_queryset)

	min_players, max_players = 12, 37
	assert int(min_players) <= session_instance.player.count() <= int(max_players), 'Недопустимое количество игроков!'

	preassigned_brokers = session_instance.player.filter(role='broker')
	preassigned_producers = session_instance.player.filter(role='producer')

	player_models_list = list(players_queryset)
	for broker in preassigned_brokers:
		player_models_list.remove(broker)
	for producer in preassigned_producers:
		player_models_list.remove(producer)

	brokers_to_distribute = session_instance.number_of_brokers - preassigned_brokers.count()

	broker_players_sample = random.sample(player_models_list, brokers_to_distribute)

	for player in players_queryset:
		for broker_player in broker_players_sample:
			if player == broker_player:
				player.role = 'broker'
				player.save()
				player_models_list.remove(broker_player)
		for remaining_player in player_models_list:
			remaining_player.role = 'producer'
			remaining_player.save()

