
from blueshift.library.technicals.indicators import rsi, bollinger_band, ema

from blueshift.api import(  symbol,
                            order_target_percent,
                            schedule_function,
                            date_rules,
                            time_rules,
                       )

def initialize(context):
    """
        A function to define things to do at the start of the strategy
    """
    # universe selection
    context.stock = symbol('HAL')

    # define strategy parameters
    context.params = {'indicator_lookback':255,
                      'indicator_freq':'5m',
                      'EMA_period_short':50,
                      'EMA_period_long':200,
                      'BBands_period':30,
                      'RSI_period':14,
                      'trade_freq':15,
                      }

    
    freq = int(context.params['trade_freq'])
    schedule_function(run_strategy, date_rules.every_day(),
                      time_rules.every_nth_minute(freq))
    
    schedule_function(stop_trading, date_rules.every_day(),
                      time_rules.market_close(minutes=15))
    
    context.trade = True
    context.trade_type = 0
    
def before_trading_start(context, data):
    context.trade = True
    
def stop_trading(context, data):
    context.trade = False

def run_strategy(context, data):
    """
        A function to define core strategy steps
    """
    if not context.trade:
        return
    
    rebalance(context, data)

def rebalance(context,data):
    """
        A function to rebalance - all execution logic goes here
    """
    try:
        px = data.history(context.stock, 'close',
            context.params['indicator_lookback'],
            context.params['indicator_freq'])
    except:
        return
    
    rsi_signal = rsi_signal_function(px, context.params)
    ema_signal = EMA_signal_function(px, context.params)
    bb_signal = bb_signal_function(px, context.params)
    if context.trade_type == 1:
        
        # Exit long 
        if bb_signal == -1:
            order_target_percent(context.stock, 0)
            context.trade_type = 0

    elif context.trade_type == -1:

        # Exit short 
        if bb_signal == 1:
            order_target_percent(context.stock, 0)
            context.trade_type = 0

    else:
        if rsi_signal == 1 and ema_signal == 1:
            order_target_percent(context.stock, 1)
            context.trade_type = 1
        elif rsi_signal == -1 and ema_signal == -1:
            order_target_percent(context.stock, -1)
            context.trade_type = -1

def rsi_signal_function(px, params):    
    """
        RSI Signal Generator
    """
    rsi_val = rsi(px, params['RSI_period'])

    if rsi_val > 70:
        return -1
    elif rsi_val < 30:
        return 1
    else:
        return 0

def EMA_signal_function(px, params): 
    """
        EMA Crossover Signal Generator
    """
    ema_short = ema(px, params['EMA_period_short'])
    ema_long = ema(px, params['EMA_period_long'])

    if ema_short - ema_long > 0:
        return 1
    elif ema_short - ema_long < 0:
        return -1
    else:
        return 0

def bb_signal_function(px, params):
    """
        Bollinger Band Signal Generator
    """
    
    upper, mid, lower = bollinger_band(px,params['BBands_period'])
    if upper - lower == 0:
        return 0

    last_px = px[-1]
    dist_to_upper = 100*(upper - last_px)/(upper - lower)

    if dist_to_upper > 95:
        return -1
    elif dist_to_upper < 5:
        return 1
    else:
        return 0

    

