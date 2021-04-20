from django.shortcuts import get_object_or_404
from rest_framework.viewsets import ModelViewSet
from rest_framework import mixins, viewsets, status
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from .models import SessionModel, PlayerModel, ProducerModel, TransactionModel, \
	BrokerModel
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from . import serializers
from .permissions import IsInSession, IsThePlayer
from rest_framework.decorators import action

from authorization.services.create_player import create_player
from authorization.permissions import IsPlayer
from authorization.serializers import PlayerWithTokenSerializer
from game.services.normal.data_access.count_session import change_phase, start_session, \
	count_session, produce_billets, send_trade, cancel_trade, end_turn, cancel_end_turn, \
	accept_transaction, deny_transaction, finish_by_player_count

from django.template import loader
from django.http import HttpResponse


# Декоратор @action. Дефолтные значениея:
# methods - GET
# url_path - НАЗВАНИЕ_МЕТОДА
# url_name - НАЗВАНИЕ-МЕТОДА
# detail - None; обязательное поле; устанавливает, применяется ли роут для retrieve (True) или list (False)


class SessionAdminViewSet(ModelViewSet):
	"""
	Обрабатывает сессии для администраторов
	"""
	queryset = SessionModel.objects.all()
	serializer_class = serializers.SessionAdminSerializer
	permission_classes = [IsAdminUser]

	@action(methods=['GET'], detail=True, url_path='start-session', permission_classes=[])
	def start_session(self, request, pk):
		"""
		Создаёт новую сессию
		"""
		session = SessionModel.objects.get(pk=pk)
		start_session(session)
		return Response({'detail': 'Session started'}, status=status.HTTP_200_OK)

	@action(methods=['PUT'], detail=True, url_path='set-turn-phase', permission_classes=[])
	def set_turn_phase(self, request, pk):
		"""
		Устанавливает фазу хода в сессии
		"""
		session = SessionModel.objects.get(pk=pk)
		phase = request.data.get('phase')
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
		queryset = self.get_queryset().filter(status='initialized')
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
			players = PlayerModel.objects.filter(session_id=session_instance.id).order_by('-balance')
			return Response(
				serializers.PlayerSerializer(players, many=True),
				status=status.HTTP_200_OK
			)
		return Response(
			{'detail': 'Сессия не завершена!'},
			status=status.HTTP_400_BAD_REQUEST
		)


class PlayerViewSet(viewsets.ModelViewSet):
	queryset = PlayerModel.objects.all()
	serializer_class = serializers.PlayerSerializer

	@action(methods=['GET'], permission_classes=[IsPlayer], detail=False)
	def me(self, request):
		return Response(self.get_serializer(request.player).data,
						status=status.HTTP_200_OK)

	@action(methods=['put'], permission_classes=[IsPlayer], detail=False,
			url_path='end-turn')
	def end_turn(self, request):
		"""
		Завершает ход
		"""
		if not request.player.session.status == 'started':
			return Response({
				'detail': 'Session is not started!'
			}, status=status.HTTP_400_BAD_REQUEST)
		end_turn(request.player)
		finish_by_player_count(request.player.session)
		return Response(status=status.HTTP_200_OK)

	@action(methods=['put'], permission_classes=[IsPlayer], detail=False,
			url_path='cancel-end-turn')
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

	@action(methods=['get'], permission_classes=[IsPlayer], detail=False)
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

	# permission_classes = [IsInSession]

	# permission_classes = [IsThePlayer]
	@action(methods=['POST'], detail=True)
	def produce(self, request, pk):
		"""
		Отправляет запрос на производство заготовок
		"""
		producer = ProducerModel.objects.get(player_id=pk)
		quantity = request.data.get('quantity')
		produce_billets(producer, quantity)
		return Response(
			{
				'detail': f'Произведено {quantity} заготовок для производителя {producer.player.nickname}.',
				'stash': serializers.ProducerSerializer(producer).data
			},
			status=status.HTTP_200_OK
		)

	@action(methods=['POST'], detail=True)
	def trade(self, request, pk):
		"""
		Отправляет маклеру предложение о сделке
		"""
		producer = ProducerModel.objects.get(player_id=pk)
		# FIXME
		broker = BrokerModel.objects.get(player_id=request.data.get('broker'))
		code = request.data.get('code')
		if broker.code == code:
			terms = request.data.get('terms')
			send_trade(producer, broker, terms)
			return Response(
				{
					'detail': f'Отправлена сделка от {producer.player.nickname} к {broker.player.nickname}',
					'terms': terms
				},
				status=status.HTTP_201_CREATED
			)
		return Response(
			{
				'detail': 'Неверный код маклера!'
			},
			status=status.HTTP_406_NOT_ACCEPTABLE
		)

	@action(methods=['delete'], detail=True, url_path='cancel-trade')
	def cancel_trade(self, request, pk):
		"""
		Отменяет сделку с маклером
		"""
		producer = ProducerModel.objects.get(player_id=pk)
		broker = BrokerModel.objects.get(player_id=request.data.get('broker'))
		cancel_trade(producer, broker)
		return Response(
			{
				'detail': f'Сделка между {producer.player.nickname} и {broker.player.nickname} отменена'
			},
			status=status.HTTP_204_NO_CONTENT
		)

	# @action(detail=True)
	# def me(self, request, pk):
	# 	"""
	# 	Отправляет полные данные о текущем игроке
	# 	"""
	# 	player = PlayerModel.objects.get(producer=pk)
	# 	return Response(
	# 		serializers.FullProducerInfoSerializer(player).data,
	# 		status=status.HTTP_200_OK
	# 	)

	@action(detail=True, url_path='balance-detail')
	def balance_detail(self, request, pk):
		"""
		Показывает детализацию баланса за предыдущий ход
		"""
		pass

	@action(detail=True, url_path='balance-history')
	def balance_history(self, request, pk):
		"""
		Показывает детализацию баланса за игру
		"""
		pass

	@action(methods=[''], detail=True, url_path='accept-show-balace')
	def accept_show_balance(self, request, pk):
		"""
		Подтверждает показ баланса маклеру
		"""
		pass

	@action(methods=[''], detail=True, url_path='deny-show-balance')
	def deny_show_balance(self, request, pk):
		"""
		Отклоняет запрос на показ баланса
		"""
		pass


class BrokerViewSet(ModelViewSet):
	queryset = BrokerModel.objects.all()
	serializer_class = serializers.BrokerSerializer

	# permission_classes = [IsInSession]

	# @action(detail=True)
	# def me(self, request, pk):
	# 	"""
	# 	Отправляет полные данные о текущем игроке
	# 	"""
	# 	broker = PlayerModel.objects.get(broker_id=pk)
	# 	return Response(
	# 		serializers.PlayerSerializer(broker).data,
	# 		status=status.HTTP_200_OK
	# 	)

	@action(methods=['put'], detail=True, url_path='accept')
	def accept_transaction(self, request, pk):
		"""
		Одобряет сделку с производителем
		"""
		producer = request.data.get('producer')
		broker = BrokerModel.objects.get(id=pk)
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
		producer = request.data.get('producer')
		broker = BrokerModel.objects.get(id=pk)
		deny_transaction(producer, broker)
		return Response(
			{
				'detail': f'Маклер {broker.player.nickname} отклонил сделку с {producer.player.nickname}'
			},
			status=status.HTTP_200_OK
		)

	@action(methods=['get'], detail=True, url_path='request-balance')
	def request_balance(self, request, pk):
		"""
		Запрашивает баланс производителя
		"""
		pass


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
		serializer = serializers.TransactionSerializer(filtered_transactions,
													   many=True)
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
		serializer = serializers.TransactionSerializer(filtered_transactions,
													   many=True)
		return Response(serializer.data, status=status.HTTP_200_OK)
