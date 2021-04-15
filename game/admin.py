from django.contrib import admin
from .models import SessionModel, PlayerModel, ProducerModel, BrokerModel, TransactionModel, BalanceDetail
from django.utils.safestring import mark_safe


@admin.register(PlayerModel)
class PlayerAdmin(admin.ModelAdmin):
    toket = admin
    list_display = (
        "id",
        "nickname",
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
    )

    def get_token(self, obj):
        return mark_safe(f'<span>{obj.token.key}</span>');

    get_token.short_description = 'Токен'


admin.site.register(SessionModel)
admin.site.register(ProducerModel)
admin.site.register(BrokerModel)
admin.site.register(TransactionModel)
admin.site.register(BalanceDetail)