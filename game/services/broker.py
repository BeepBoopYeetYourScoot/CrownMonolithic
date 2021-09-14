class AbstractBroker:

    def count_fixed_costs(self):
        """
        Считает постоянные расходы Маклера
        """
        pass

    def count_variable_costs(self):
        """
        Считает затраты Маклера на покупку заготовок
        """
        pass

    def count_proceeds(self, market_price):
        """
        Считает выручку Маклера за продажу заготовок
        """
        pass
