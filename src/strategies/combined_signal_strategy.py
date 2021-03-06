import pandas as pd
import numpy as np
import math
import datetime
from datetime import timedelta

import backtrader as bt
from numpy.random import seed
import src.utils.func_utils as func_utils
from src.strategies.log_strategy import LogStrategy


class CombinedSignalStrategy(LogStrategy):
    """
    This class defines a buy-sell strategy based on the combination of moving averages,
    for which it gets a signal by the weighted sum of different signals
    """

    w = []
    buy_threshold = None
    sell_threshold = None
    period_list = []
    moving_average_rules = []
    moving_averages = {}
    normalization = None

    optimizer = None
    gen_representation = None


    def __init__(self):
        """ CombinedSignalStrategy Class Initializer """
        super().__init__()


    def next(self):
        """ Define logic in each iteration """
        self.update_log_values()

        # we cannot send a 2nd an order if if another one is pending
        if self.order:
            return

        # ReTrain optimization algorithm
        if self.optimizer != None and len(self) % 30 == 0:
            #from_date = self.data.datetime.date().replace(year = self.data.datetime.date().year -1)
            from_date = self.data.datetime.date() - timedelta(days=180)
            to_date = self.data.datetime.date() - timedelta(days=1)

            # Reset best cost
            self.optimizer.swarm.best_cost = 0

            # Optimize weights
            kwargs={'from_date': from_date, 'to_date': to_date}
            best_cost, best_pos = self.optimizer.optimize(self.gen_representation.cost_function, iters=50, **kwargs)

            self.w, self.buy_threshold, self.sell_threshold = func_utils.get_split_w_threshold(best_pos, self.normalization)

        # Get combined signal
        final_signal = func_utils.get_combined_signal(self.moving_average_rules, self.moving_averages, self.w, len(self)-1)

        # Buy if signal is greater than buy threshold
        if not self.position and final_signal > self.buy_threshold:
            self.buy()

        # Sell if singal is smaller than sell threshold
        elif self.position and final_signal < self.sell_threshold:
            self.sell()
