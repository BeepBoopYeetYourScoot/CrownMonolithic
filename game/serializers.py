from rest_framework import serializers
from .models import SessionModel, PlayerModel, ProducerModel, BrokerModel, TransactionModel, BalanceDetail


class LobbySerializer(serializers.ModelSerializer):
	"""
	Сериализатор для юзерского вида списка сессий
	"""
	player_count = serializers.IntegerField(source='player.count', read_only=True)

	class Meta:
		model = SessionModel
		fields = [
			'id',
			'name',
			'game_type',
			'status',
			'player_count',
			'current_turn',
			'turn_phase',
		]
		read_only = [
			'__all__',
			'player_count'
		]


class SessionAdminSerializer(serializers.ModelSerializer):
	"""
	Сериализатор для администрирования запущенных сессий
	"""
	player_count = serializers.IntegerField(source='player.count', read_only=True)
	players_finished_turn = serializers.SerializerMethodField(
		source='get_players_finished_turn', read_only=True)

	class Meta:
		model = SessionModel
		fields = [
			'id',
			'name',
			'game_type',
			'turn_count',
			'number_of_brokers',
			'crown_balance',
			'status',
			'broker_starting_balance',
			'producer_starting_balance',
			'transaction_limit',
			'current_turn',
			'turn_phase',
			'player_count',
			'players_finished_turn',
		]
		read_only = [
			'__all__',
			# 'player_count',
			# 'players_finished_turn',
		]

	@staticmethod
	def get_session_player_count(instance):
		return PlayerSerializer(
			instance.player.all(),
			many=True
		)

	@staticmethod
	def get_players_finished_turn(instance):
		return instance.player.filter(ended_turn=True).count()


class PlayerSerializer(serializers.ModelSerializer):
	"""
	Сериализатор для игрока
	"""
	role_info = serializers.SerializerMethodField('get_role_info')

	class Meta:
		model = PlayerModel
		fields = [
			'id',
			'session',
			'nickname',
			'role',
			'role_name',
			'city',
			'balance',
			'ended_turn',
			'is_bankrupt',
			'status',
			'position',
			'role_info',
		]
		read_only = [
			'id',
			'status',
			'position'
		]

	@staticmethod
	def get_role_info(player_instance):
		roles = {
			'broker': {'model': BrokerModel, 'serializer': BrokerSerializer},
			'producer': {'model': ProducerModel, 'serializer': ProducerSerializer}
		}
		if player_instance.role == 'unassigned':
			return 'unassigned'

		try:
			model = roles[player_instance.role]['model'].objects.get(player=player_instance.id)
			return roles[player_instance.role]['serializer'](model).data
		except roles[player_instance.role]['model'].DoesNotExist:
			return 'not created'


class ProducerSerializer(serializers.ModelSerializer):
	transactions = serializers.SerializerMethodField('get_producer_transactions')

	class Meta:
		model = ProducerModel
		fields = [
			'id',
			'player',
			'billets_produced',
			'billets_stored',
			'transactions'
		]
		read_only = [
			'player'
		]

	@staticmethod
	def get_producer_transactions(instance):
		transactions = instance.transaction.filter(
			producer=instance.id,
			turn=instance.player.session.current_turn
		)
		return TransactionSerializer(transactions, many=True).data


class BrokerSerializer(serializers.ModelSerializer):
	transactions = serializers.SerializerMethodField('get_broker_transactions')

	class Meta:
		model = BrokerModel
		fields = '__all__'
		read_only = '__all__'

	# FIXME: optimize me, please
	def get_broker_transactions(self, instance):
		transactions = {}
		transactions['active_transactions'] = TransactionSerializer(
			instance.transaction.filter(
				broker=instance.id,
				turn=instance.player.session.current_turn,
				status='active'

			),
			many=True
		).data
		for turn in range(1, instance.player.session.current_turn + 1):
			transactions[turn] = TransactionSerializer(
				instance.transaction.filter(
					broker=instance.id,
					turn=turn,
					status__in=['accepted', 'denied']
				),
				many=True
			).data

		return transactions


class TransactionSerializer(serializers.ModelSerializer):
	class Meta:
		model = TransactionModel
		fields = '__all__'
		read_only = [
			'id',
			'session',
			'transporting_cost',
			'turn'
		]
		extra_kwargs = {
			'session': {
				'required': False,
			}
		}


class FullProducerInfoSerializer(serializers.ModelSerializer):
	"""
	Выдаёт полную информацию об игроке-производителе
	"""
	stash_info = serializers.SerializerMethodField(source='get_stash_info', read_only=True)

	class Meta:
		model = PlayerModel
		fields = [
			'id',
			'nickname',
			'role',
			'city',
			'balance',
			'is_bankrupt',
			'ended_turn',
			'status',
			'stash_info'
		]

	@staticmethod
	def get_stash_info(instance):
		"""
		Добавляет к сериализатору игрока-производителя информацию о хранилище
		"""
		stash = ProducerSerializer(
			instance.producer
		).data
		# fields('billets_produced', 'billets_stored')
		return stash


class BrokerBalanceDetailSerializer(serializers.ModelSerializer):
	class Meta:
		model = BalanceDetail
		fields = [
			'start_turn_balance',
			'end_turn_balance',
			'purchase_blanks',
			'logistics',
			'blanks',
			'fine',
			'crown',
		]


class ProducerBalanceDetailSerializer(serializers.ModelSerializer):
	class Meta:
		model = BalanceDetail
		fields = [
			'start_turn_balance',
			'end_turn_balance' ,
			'sales_income',
			'fixed_costs',
			'variable_costs',
			'raw_stuff_costs',
			'fine',
			'storage',
			'logistics',
		]
