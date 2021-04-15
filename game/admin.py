from django.contrib import admin
from .models import SessionModel, PlayerModel, ProducerModel, BrokerModel, TransactionModel, BalanceDetail
from django.utils.safestring import mark_safe
from django.urls import reverse


@admin.register(PlayerModel)
class PlayerAdmin(admin.ModelAdmin):
    token = admin
    list_display = (
        "id",
        "nickname",
        "get_token",
        "session_link",
        "role_link",
        "city",
        "balance",
        "ended_turn",
        "is_bankrupt",
    )

    list_display_links = (
        "nickname",
    )

    list_filter = (
        'session',
    )

    def get_token(self, obj):
        return mark_safe(f'<span>{obj.token.key}</span>');

    get_token.short_description = 'Токен'

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



admin.site.register(SessionModel)
admin.site.register(ProducerModel)
admin.site.register(BrokerModel)
admin.site.register(TransactionModel)
admin.site.register(BalanceDetail)
