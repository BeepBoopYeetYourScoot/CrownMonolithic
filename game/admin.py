from django.contrib import admin
from .models import SessionModel, PlayerModel, ProducerModel, BrokerModel, \
    TransactionModel, BalanceDetail, BalanceRequest, TurnTime
from django.utils.safestring import mark_safe
from django.urls import reverse
from .services.normal.data_access import count_session


@admin.register(PlayerModel)
class PlayerAdmin(admin.ModelAdmin):
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
        for session in queryset:
            count_session.start_session(session)

    def finish_session(self, request, queryset):
        for session in queryset:
            count_session.finish_session(session)

    def finish_turn(self, request, queryset):
        for session in queryset:
            session.turn_phase = 'transaction'
            count_session.count_session(session)

    def next_phase(self, request, queryset):
        for session in queryset:
            if session.turn_phase == 'negotiation':
                count_session.change_phase(session, 'transaction')
            elif session.turn_phase == 'transaction':
                count_session.count_session(session)

    def fill_session(self, request, queryset):
        for session in queryset:
            for i in range(12):
                PlayerModel.objects.create(session_id=session.id, nickname=f'{i}')

    fill_session.short_description = 'Заполнить сессию'
    start_session.short_description = 'Начать сесиию'
    next_phase.short_description = 'Завершить фазу'
    finish_turn.short_description = 'Завершить ход'
    finish_session.short_description = 'Завершить сессию'
    actions = [fill_session, start_session, next_phase, finish_turn, finish_session]

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
        return mark_safe(f'<span>{obj.token.key}</span>')

    get_token.short_description = 'Токен'


@admin.register(BalanceDetail)
class BalanceDetailAdmin(admin.ModelAdmin):
    list_display = (
        'player',
        'get_role_name',
        'get_session',
    )

    def get_session(self, obj):
        return mark_safe(f'<span>{obj.player.session}</span>')

    get_session.short_description = 'Сессия'

    def get_role_name(self, obj):
        return mark_safe(f'<span>{obj.player.role_name}</span>')

    get_role_name.short_description = 'Игровое имя'


admin.site.register(ProducerModel)
admin.site.register(BrokerModel)
admin.site.register(TransactionModel)
admin.site.register(BalanceRequest)
admin.site.register(TurnTime)
