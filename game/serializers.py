from rest_framework import serializers
from .models import SessionModel, PlayerModel, ProducerModel, BrokerModel, \
    TransactionModel, BalanceDetail, BalanceRequest
from django.db.models import Sum


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
            'allow_show_balance',
            'allow_show_transaction_sum'
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
            'map_url',
            'logistics_url',
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
            'position',
            'map_url'
            'logistics_url'
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


class PlayerResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerModel
        fields = [
            'id',
            'nickname',
            'role',
            'role_name',
            'balance',
            'is_bankrupt',
            'status',
            'position',
        ]
        read_only = '__all__'


class ProducerSerializer(serializers.ModelSerializer):
    transactions = serializers.SerializerMethodField('get_producer_transactions')
    nickname = serializers.CharField(source='player.nickname')

    class Meta:
        model = ProducerModel
        fields = [
            'id',
            'nickname',
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
    transactions = serializers.SerializerMethodField('get_transactions')
    previous_turn_transactions = serializers \
        .SerializerMethodField('get_previous_transactions')
    pushared_billets = serializers.SerializerMethodField('get_pushared_billets')

    class Meta:
        model = BrokerModel
        fields = '__all__'
        read_only = '__all__'

    # FIXME: optimize me, please
    def get_transactions(self, instance):
        return TransactionSerializer(
            instance.transaction.filter(
                broker=instance.id,
                turn=instance.player.session.current_turn,
            ),
            many=True
        ).data

    def get_previous_transactions(self, instance):
        current_turn = instance.player.session.current_turn
        if current_turn < 2:
            return []

        return TransactionSerializer(
            instance.transaction.filter(
                broker=instance.id,
                turn=current_turn - 1,
            ),
            many=True
        ).data

    # FIXME: оптимизируй меня... или убей
    def get_pushared_billets(self, instance):
        pushared_billets = instance.transaction \
            .filter(turn=instance.player.session.current_turn, status='accepted') \
            .aggregate(pushared_billets=Sum('quantity')) \
            .get('pushared_billets', 0)
        return pushared_billets if pushared_billets else 0


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
            'end_turn_balance',
            'sales_income',
            'fixed_costs',
            'variable_costs',
            'raw_stuff_costs',
            'fine',
            'storage',
            'logistics',
        ]


class BalanceRequestSerializer(serializers.ModelSerializer):
    broker_nickname = serializers.CharField()
    broker_role_name = serializers.CharField()

    class Meta:
        model = BalanceRequest
        exclude = [
            'id',
            'turn'
        ]


class ProducerBalanceSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nickname = serializers.CharField()
    role_name = serializers.CharField()
    balance = serializers.IntegerField()
