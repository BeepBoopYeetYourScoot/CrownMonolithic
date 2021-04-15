from django.contrib import admin
from .models import SessionModel, PlayerModel, ProducerModel, BrokerModel, TransactionModel, BalanceDetail
from django.utils.safestring import mark_safe
from django.urls import reverse

from .services.normal.data_access.count_session import count_session


@admin.register(PlayerModel)
class PlayerAdmin(admin.ModelAdmin):
<<<<<<< HEAD
	toket = admin
	list_display = (
		"nickname",
		"id",
		"get_token",
		"session",
		"role",
		"city",
		"balance",
		"ended_turn",
		"is_bankrupt",
	)

	list_filter = (
		'session',
		'role',
		'is_bankrupt',
		'ended_turn'
	)

	def make_bankrupt(self, request, queryset):
		queryset.update(is_bankrupt=True)

	make_bankrupt.short_description = 'Обанкротить'

	def force_end_turn(self, request, queryset):
		queryset.update(ended_turn=True)

	force_end_turn.short_description = 'Завершить ход'

	def cancel_bankruptcy(self, request, queryset):
		queryset.update(is_bankrupt=False)

	cancel_bankruptcy.short_description = 'Отменить банкротство'

	actions = [make_bankrupt, force_end_turn, cancel_bankruptcy]

	def get_token(self, obj):
		return mark_safe(f'<span>{obj.token.key}</span>')

	get_token.short_description = 'Токен'


@admin.register(SessionModel)
class SessionAdmin(admin.ModelAdmin):
	list_display = (
		"name",
		"id",
		"game_type",
		"status",
		"turn_count",
		"number_of_brokers",
		"producer_starting_balance",
		"broker_starting_balance",
		"crown_balance",
		"current_turn",
		"turn_phase"
	)

	list_filter = (
		'game_type',
		'status'
	)

	def start_session(self, request, queryset):
		queryset.update(status='started')

	def finish_session(self, request, queryset):
		queryset.update(status='finished')

	def finish_turn(self, request, queryset):
		for session in queryset:
			session.turn_phase = 'transaction'
			count_session(session)

	start_session.short_description = 'Начать сесиию'
	finish_session.short_description = 'Завершить сессию'
	finish_turn.short_description = 'Завершить ход'

	actions = [start_session, finish_session, finish_turn]

	def role_link(self, obj):
		role_id = obj.producer.id if obj.role == 'producer' else obj.broker.id
		return mark_safe('<a href="{}">{}</a>'.format(
			reverse("admin:game_{}model_change".format(str(obj.role)), args=(role_id,)),
			obj.role
		))

	role_link.short_description = 'Роль'

	def session_link(self, obj):
		return mark_safe('<a href="{}">{}</a>'.format(
			reverse("admin:game_sessionmodel_change", args=(obj.session_id,)),
			obj.session.name
		))

	session_link.short_description = 'Сессия'

	def get_token(self, obj):
		return mark_safe(f'<span>{obj.token.key}</span>');

	get_token.short_description = 'Токен'


admin.site.register(ProducerModel)
admin.site.register(BrokerModel)
admin.site.register(TransactionModel)
admin.site.register(BalanceDetail)
