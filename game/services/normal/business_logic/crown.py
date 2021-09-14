class CrownNormal:
    def __init__(self, balance):
        self.balance = balance

    def count_market_price(self, market_volume):
        """Подсчитывает рыночную стоимость одной заготовки """
        if market_volume == 0:
            return 160
        return self.balance / market_volume

    def update_balance(self, market_volume):
        """Обновляет баланс Короны на следующий ход"""
        if market_volume < 90:
            self.balance *= 1.1
        else:
            self.balance *= 0.97
        return
