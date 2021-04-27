from django.db.models import Subquery, F
from rest_framework.viewsets import ModelViewSet
from rest_framework import mixins, viewsets, status
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from .models import SessionModel, PlayerModel, ProducerModel, TransactionModel, \
	BrokerModel, BalanceRequest
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from . import serializers
from .permissions import IsThePlayer
from rest_framework.decorators import action

from authorization.services.create_player import create_player
from authorization.permissions import IsPlayer
from authorization.serializers import PlayerWithTokenSerializer
from game.services.normal.data_access.count_session import change_phase, \
	start_session, count_session, produce_billets, send_trade, cancel_trade, \
	end_turn, cancel_end_turn, accept_transaction, deny_transaction,\
	create_balance_request, accept_balance_request, \
	deny_balance_request, finish_session

# from websockets.services import finish_turn_by_players

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

import requests

# Декоратор @action. Дефолтные значениея:
# methods - GET
# url_path - НАЗВАНИЕ_МЕТОДА
# url_name - НАЗВАНИЕ-МЕТОДА
# detail - None; обязательное поле; устанавливает, применяется ли роут для retrieve (True) или list (False)

# BASE_URL = 'http://0.0.0.0:8000/change/'


class SessionAdminViewSet(ModelViewSet):
	"""
	Обрабатывает сессии для администраторов
	"""
	queryset = SessionModel.objects.all()
	serializer_class = serializers.SessionAdminSerializer

	# permission_classes = [IsAdminUser]

	@action(methods=['GET'], detail=True, url_path='start-session', permission_classes=[])
	def start_session(self, request, pk):
		"""
		Создаёт новую сессию
		"""
		session = SessionModel.objects.get(pk=pk)
		start_session(session)
		# requests.get('http://0.0.0.0:8000/start/')
		return Response({'detail': 'Session started'}, status=status.HTTP_200_OK)

	@swagger_auto_schema(
		request_body=openapi.Schema(
			type=openapi.TYPE_OBJECT,
			required=['phase'],
			properties={
				'phase': openapi.Schema(
					type=openapi.TYPE_STRING,
					description='Этап игры. Варианты: "negotiation" или "transaction"'
				),
			},
		),
		responses={'200': 'Success', '400': 'Wrong phase!'})
	@action(methods=['PUT'], detail=True, url_path='set-turn-phase', permission_classes=[])
	def set_turn_phase(self, request, pk):
		"""
		Устанавливает фазу хода в сессии
		"""
		session = SessionModel.objects.get(pk=pk)
		phase = request.data.get('phase')
		if not phase in ['negotiation', 'transaction']:
			return Response({'detail': 'Wrong phase!'}, status=status.HTTP_400_BAD_REQUEST)
		change_phase(session, phase)
		return Response({'detail': 'Phase updated'}, status=status.HTTP_200_OK)

	@action(methods=['GET'], detail=True, renderer_classes=[JSONRenderer], url_path='count-session',
			permission_classes=[])
	def count_session(self, request, pk):
		"""
		Запускает пересчёт хода
		"""
		session_instance = SessionModel.objects.get(pk=pk)
		if session_instance.status == 'initialized':
			return Response({'detail': 'Session is not started yet!'}, status=status.HTTP_400_BAD_REQUEST)
		if session_instance.status == 'finished':
			return Response({'detail': 'Session is already finished!'}, status=status.HTTP_400_BAD_REQUEST)
		count_session(session_instance)
		return Response({'detail': 'Session counted'}, status=status.HTTP_200_OK)

	@action(methods=['get'], detail=True, url_path='finish-session', permission_classes=[])
	def finish_session(self, request, pk):
		"""
		Завершает сессию
		"""
		session_instance = SessionModel.objects.get(pk=pk)
		if session_instance.status == 'started':
			finish_session(session_instance)
			# requests.get('http://0.0.0.0:8000/start/')
			return Response({'detail': 'Session finished'}, status=status.HTTP_200_OK)
		return Response({'detail': 'Session has wrong status'}, status=status.HTTP_400_BAD_REQUEST)


class LobbyViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.ListModelMixin):
	"""
	Для просмотра списка лобби и операциями с единичным лобби
	"""
	queryset = SessionModel.objects.all()
	serializer_class = serializers.LobbySerializer

	# permission_classes = [IsAuthenticated]

	def list(self, request, *args, **kwargs):
		"""
		Выдаёт список с созданными администратором сессиями
		"""
		queryset = self.queryset.filter(status='initialized')
		serializer = serializers.LobbySerializer(queryset, many=True)
		return Response(serializer.data, status=status.HTTP_200_OK)

	def retrieve(self, request, *args, **kwargs):
		"""
		Выдаёт информацию о конкретном лобби
		"""
		instance = self.get_object()
		serializer = self.get_serializer(instance)
		players_in_lobby = PlayerModel.objects.filter(session_id=instance.id)
		return Response(
			{
				'lobby': serializer.data,
				'players': serializers.PlayerSerializer(players_in_lobby, many=True).data
			},
			status=status.HTTP_200_OK
		)

	@action(methods=['post'], detail=True, url_path='join')
	def join_session(self, request, pk):
		"""
		Даёт игроку авторизоваться и присоединиться к сессии
		"""
		if hasattr(request, 'player'):
			return Response({'detail': 'You\'re already a player!'},
							status=status.HTTP_400_BAD_REQUEST)
		try:
			session = SessionModel.objects.get(id=pk)
			assert session.status == 'initialized'
			nickname = request.data.get('nickname')
			player = create_player(session, nickname)

			# requests.get(BASE_URL)
			return Response(PlayerWithTokenSerializer(player).data,
							status=status.HTTP_201_CREATED)
		except SessionModel.DoesNotExist:
			return Response({'detail': 'No such session!'},
							status=status.HTTP_400_BAD_REQUEST)
		except  AssertionError:
			return Response({'detail': 'Session is already started!'},
							status=status.HTTP_400_BAD_REQUEST)

	@action(methods=['delete'], detail=True, url_path='leave')
	def leave_session(self, request, pk):
		"""
		Выкидывает игрока из сессии
		"""
		try:
			session_instance = SessionModel.objects.get(pk=pk)
			assert request.player.session.id == session_instance.id, "Вы не в той сессии"
			request.player.delete()
			# requests.get(BASE_URL)
			return Response(status=status.HTTP_204_NO_CONTENT)
		except SessionModel.DoesNotExist:
			return Response({'detail': 'No such session'},
							status=status.HTTP_400_BAD_REQUEST)
		except AssertionError:
			return Response({'detail': 'You\'re not in this session'},
							status=status.HTTP_400_BAD_REQUEST)

	@action(detail=True, url_path='results')
	def show_results(self, request, pk):
		"""
		Показывает список игроков согласно балансу
		"""
		session_instance = SessionModel.objects.get(pk=pk)
		if session_instance.status == 'finished':
			players = PlayerModel.objects \
				.filter(session_id=session_instance.id) \
				.order_by('is_bankrupt', '-balance')
			return Response(
				serializers.PlayerResultSerializer(players, many=True).data,
				status=status.HTTP_200_OK
			)
		return Response(
			{'detail': 'Сессия не завершена!'},
			status=status.HTTP_400_BAD_REQUEST
		)


class PlayerViewSet(viewsets.ModelViewSet):
	queryset = PlayerModel.objects.all()
	serializer_class = serializers.PlayerSerializer
	permission_classes = [IsPlayer]

	@action(methods=['GET'], detail=False)
	def me(self, request):
		return Response(self.get_serializer(request.player).data,
						status=status.HTTP_200_OK)

	@action(methods=['put'], detail=False, url_path='end-turn')
	def end_turn(self, request):
		"""
		Завершает ход
		"""
		if not request.player.session.status == 'started':
			return Response({
				'detail': 'Session is not started!'
			}, status=status.HTTP_400_BAD_REQUEST)
		end_turn(request.player)
		return Response(status=status.HTTP_200_OK)

	@action(methods=['put'], detail=False, url_path='cancel-end-turn')
	def cancel_end_turn(self, request):
		"""
		Завершает ход
		"""
		if not request.player.session.status == 'started':
			return Response({
				'detail': 'Session is not started!'
			}, status=status.HTTP_400_BAD_REQUEST)
		cancel_end_turn(request.player)
		return Response(status=status.HTTP_200_OK)

	@action(methods=['get'], detail=False)
	def balance_detail(self, request):
		if not request.player.session.status == 'started':
			return Response({'detail': 'Session is not started or finished!'}, status=status.HTTP_400_BAD_REQUEST)
		if request.player.session.current_turn == 1:
			return Response({'detail': 'There is no detail on first turn!'}, status=status.HTTP_400_BAD_REQUEST)
		serializer = serializers.ProducerBalanceDetailSerializer if request.player.role == 'producer' \
			else serializers.BrokerBalanceDetailSerializer
		return Response(serializer(request.player.detail).data, status=status.HTTP_200_OK)


class ProducerViewSet(ModelViewSet):
	queryset = ProducerModel.objects.all()
	serializer_class = serializers.ProducerSerializer
	permission_classes = [IsPlayer]

	@action(methods=['POST'], detail=True)
	def produce(self, request, pk):
		"""
		Отправляет запрос на производство заготовок
		"""
		producer = ProducerModel.objects.get(player_id=request.data.get("producer_player"))
		quantity = request.data.get('quantity')
		produce_billets(producer, quantity)
		return Response(
			{
				'detail': f'Произведено {quantity} заготовок для производителя {producer.player.nickname}.',
				'stash': serializers.ProducerSerializer(producer).data
			},
			status=status.HTTP_200_OK
		)

	@action(methods=['POST'], detail=True, permission_classes=[])
	def trade(self, request, pk):
		"""
		Отправляет маклеру предложение о сделке
		"""
		producer = ProducerModel.objects.get(id=request.data.get('producer_player'))
		broker = BrokerModel.objects.get(id=request.data.get('broker_player'))
		# code = request.data.get('code')
		# if broker.code == code:
		terms = request.data.get('terms')
		send_trade(producer, broker, terms)
		return Response(
			{
				'detail': f'Отправлена сделка от {producer.player.nickname}'
						  f'к {broker.player.nickname}',
				'Условия': terms
			},
			status=status.HTTP_201_CREATED
		)

	# return Response(
	# 	{
	# 		'detail': 'Неверный код маклера!'
	# 	},
	# 	status=status.HTTP_406_NOT_ACCEPTABLE
	# )

	@action(methods=['delete'], detail=True, url_path='cancel-trade')
	def cancel_trade(self, request, pk):
		"""
		Отменяет сделку с маклером
		"""
		producer = ProducerModel.objects.get(id=request.data.get('producer_player'))
		broker = BrokerModel.objects.get(id=request.data.get('broker_player'))
		cancel_trade(producer, broker)
		return Response(
			{
				'detail': f'Сделка между {producer.player.nickname} и {broker.player.nickname} отменена'
			},
			status=status.HTTP_204_NO_CONTENT
		)

	@swagger_auto_schema(responses={'200': 'OK'})
	@action(methods=['get'], detail=False, url_path='received-balance-requests',
			url_name='received_balance_requests_list')
	def get_balance_requests_list(self, request):
		"""
		Получает список не рассмотренных запросов
		"""
		requests = request.player.producer.received_balance_requests \
			.filter(turn=request.player.session.current_turn, status='active') \
			.annotate(
			broker_role_name=F('broker__player__role_name')
		)
		print(requests.query)
		serializer = serializers.BalanceRequestSerializer(requests, many=True)
		return Response(serializer.data, status=status.HTTP_200_OK)

	@swagger_auto_schema(
		request_body=openapi.Schema(
			type=openapi.TYPE_OBJECT,
			required=['broker'],
			properties={
				'broker': openapi.Schema(
					type=openapi.TYPE_INTEGER,
					description='Player id'
				),
			},
		),
		responses={'200': 'Success', '404': 'Bad broker'})
	@action(methods=['put'], detail=False, url_path='accept-balance-request')
	def accept_show_balance(self, request):
		"""
		Подтверждает показ баланса маклеру
		"""
		try:
			broker = BrokerModel.objects.get(player=request.data.get('broker'))
		except BrokerModel.DoesNotExist:
			return Response({'detail': 'No such broker'},
							status=status.HTTP_400_BAD_REQUEST)

		accept_balance_request(request.player.producer, broker)
		return Response(status=status.HTTP_200_OK)

	@swagger_auto_schema(
		request_body=openapi.Schema(
			type=openapi.TYPE_OBJECT,
			required=['broker'],
			properties={
				'broker': openapi.Schema(
					type=openapi.TYPE_INTEGER,
					description='Player id'
				),
			},
		),
		responses={'204': 'Success', '404': 'Bad broker'})
	@action(methods=['put'], detail=False, url_path='deny-balance-request')
	def deny_show_balance(self, request):
		"""
		Отклоняет запрос на показ баланса
		"""
		try:
			broker = BrokerModel.objects.get(player=request.data.get('broker'))
		except BrokerModel.DoesNotExist:
			return Response({'detail': 'No such broker'},
							status=status.HTTP_400_BAD_REQUEST)

		deny_balance_request(request.player.producer, broker)
		return Response(status=status.HTTP_204_NO_CONTENT)


class BrokerViewSet(ModelViewSet):
	queryset = BrokerModel.objects.all()
	serializer_class = serializers.BrokerSerializer

	@action(methods=['put'], detail=True, url_path='accept')
	def accept_transaction(self, request, pk):
		"""
		Одобряет сделку с производителем
		"""
		producer = ProducerModel.objects.get(id=request.data.get('producer_player'))
		broker = BrokerModel.objects.get(id=request.data.get('broker_player'))
		accept_transaction(producer, broker)
		return Response(
			{
				'detail': f'Маклер {broker.player.nickname} одобрил сделку с {producer.player.nickname}'
			},
			status=status.HTTP_200_OK
		)

	@action(methods=['put'], detail=True, url_path='deny')
	def deny_transaction(self, request, pk):
		"""
		Отклоняет сделку с производителем
		"""
		producer = ProducerModel.objects.get(id=request.data.get('producer_player'))
		broker = BrokerModel.objects.get(id=request.data.get('broker_player'))
		deny_transaction(producer, broker)
		return Response(
			{
				'detail': f'Маклер {broker.player.nickname} отклонил сделку с {producer.player.nickname}'
			},
			status=status.HTTP_200_OK
		)

	@swagger_auto_schema(
		request_body=openapi.Schema(
			type=openapi.TYPE_OBJECT,
			required=['producer'],
			properties={
				'producer': openapi.Schema(type=openapi.TYPE_INTEGER),
			},
		),
		responses={'201': 'Created', '400': 'Error'}
	)
	@action(methods=['post'], detail=False, url_path='request-balance')
	def request_balance(self, request):
		"""
		Запрашивает баланс производителя
		"""
		try:
			producer = ProducerModel.objects \
				.get(player=request.data.get('producer'))
		except ProducerModel.DoesNotExist:
			return Response({'detail': 'No such producer'},
							status=status.HTTP_400_BAD_REQUEST)

		create_balance_request(producer, request.player.broker)
		return Response(status=status.HTTP_201_CREATED)

	@swagger_auto_schema(responses={'200': 'OK'})
	@action(methods=['get'], detail=False, url_path='producer-balances',
			url_name='get_accepted_balance_requests')
	def get_accepted_balance_requests(self, request):
		requests = BalanceRequest.objects.filter(
			broker=request.player.broker,
			status='accepted',
			turn=request.player.session.current_turn
		).values('producer')
		# TODO: проверить не лучше ли через annotate
		producer_players = PlayerModel.objects.filter(
			session=request.player.session,
			producer__in=Subquery(requests)
		).only('role_name', 'nickname', 'balance')

		serializer = serializers.ProducerBalanceSerializer(producer_players, many=True)
		return Response(serializer.data, status=status.HTTP_200_OK)


class TransactionViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin,
						 mixins.UpdateModelMixin, mixins.ListModelMixin):
	queryset = TransactionModel.objects.all()
	serializer_class = serializers.TransactionSerializer
	permission_classes = [IsPlayer]

	@action(methods=['get'], detail=False)
	def current_turn_transactions(self, request):
		try:
			transactions = request.player.broker.transaction
		except BrokerModel.DoesNotExist:
			transactions = request.player.producer.transaction

		filtered_transactions = transactions.filter(
			turn=request.player.session.current_turn
		)
		serializer = serializers.TransactionSerializer(filtered_transactions, many=True)
		return Response(serializer.data, status=status.HTTP_200_OK)

	@action(methods=['get'], detail=False)
	def previous_turn_transactions(self, request):
		try:
			transactions = request.player.broker.transaction
		except BrokerModel.DoesNotExist:
			transactions = request.player.producer.transaction

		filtered_transactions = transactions.filter(
			turn=request.player.session.current_turn - 1
		)
		serializer = serializers.TransactionSerializer(filtered_transactions, many=True)
		return Response(serializer.data, status=status.HTTP_200_OK)
