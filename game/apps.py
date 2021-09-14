from django.apps import AppConfig


class GameConfig(AppConfig):
	name = 'game'

	def ready(self):
		from websockets import services
		from game import signals
