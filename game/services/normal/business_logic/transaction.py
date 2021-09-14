from game.models import TransactionModel


class TransactionNormal:
    def __init__(self, transaction: TransactionModel):
        self.producer = transaction.producer.player_id
        self.broker = transaction.broker.player_id
        self.quantity = transaction.quantity
        self.price = transaction.price
        self.transporting_cost = transaction.transporting_cost
        self.paid = False
        self.delivered = 0

    transaction_limit = 2000
