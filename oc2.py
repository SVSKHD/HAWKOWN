import MetaTrader5 as mt5
import time
from datetime import datetime
import numpy as np

data = {
	'login': 213031600,
	'password': "pYP@%ga9",
	'server': "OctaFX-Demo",
}

target = None

MOVEMENT_THRESHOLD = 0.0001  # Threshold for detecting significant movement
VOLUME_THRESHOLD = 500  # Example threshold for minimum volume


def get_balance_and_target():
	global target
	account_info = mt5.account_info()
	if account_info:
		if account_info.balance < 0:
			print(f"Your Account balance is negative {account_info.balance}")
		else:
			target = round((account_info.balance * 1) / 100, 2)
			print(f"Your Account Balance {account_info.balance}. You can trade, today's target is {target}")


def get_candles(symbol, timeframe=mt5.TIMEFRAME_M1, count=5):
	"""
	Retrieve the latest candle data. Analyze multiple candles to confirm the trend.
	"""
	candles = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
	
	if candles is None or len(candles) == 0:
		print(f"Failed to retrieve candles for {symbol} in timeframe {timeframe}")
		return None
	
	for candle in candles:
		candle['time_str'] = datetime.fromtimestamp(candle['time']).strftime('%Y-%m-%d %H:%M:%S')
	
	return candles


def analyze_partial_candles(symbol, timeframe=mt5.TIMEFRAME_M1, count=5):
	"""
	Analyze multiple partial candles to confirm potential market direction.
	"""
	candles = get_candles(symbol, timeframe, count)
	
	if candles is None:
		return None
	
	upward_trend = 0
	downward_trend = 0
	for candle in candles:
		open_price = candle['open']
		current_price = candle['close']  # This will change as the candle isn't closed yet
		
		if current_price > open_price:
			upward_trend += 1
		elif current_price < open_price:
			downward_trend += 1
	
	# Determine dominant trend based on the majority of partial candles
	if upward_trend > downward_trend:
		print(f"Potential upward trend: {upward_trend} candles are moving up.")
		return "BUY"
	elif downward_trend > upward_trend:
		print(f"Potential downward trend: {downward_trend} candles are moving down.")
		return "SELL"
	else:
		print("No clear trend detected.")
		return "HOLD"


def monitor_real_time_price(symbol):
	"""
	Monitors real-time tick data to detect potential early moves,
	filtering out insignificant price changes.
	"""
	previous_price = None
	last_signal_time = 0
	min_time_between_signals = 5  # seconds
	
	while True:
		tick = mt5.symbol_info_tick(symbol)
		
		if tick is None:
			print(f"Failed to retrieve tick data for {symbol}")
			continue
		
		bid_price = tick.bid
		
		if previous_price is not None:
			# Calculate the price difference in pips
			price_difference = abs(bid_price - previous_price)
			
			# Only react to price changes that are greater than the threshold
			if price_difference >= MOVEMENT_THRESHOLD:
				current_time = time.time()
				
				# Avoid sending signals too frequently
				if current_time - last_signal_time > min_time_between_signals:
					if bid_price > previous_price:
						print(f"Significant upward movement detected: Bid = {bid_price}")
						return "BUY"
					elif bid_price < previous_price:
						print(f"Significant downward movement detected: Bid = {bid_price}")
						return "SELL"
				
				last_signal_time = current_time
		
		previous_price = bid_price
		time.sleep(1)  # Adjust frequency as needed


def check_volume(candle):
	"""
	Check if the trading volume meets the minimum volume threshold.
	"""
	if candle['tick_volume'] >= VOLUME_THRESHOLD:
		return True
	else:
		print(f"Volume too low: {candle['tick_volume']}")
		return False


def loop_through():
	while True:
		latest_price = get_live_price('EURUSD')
		
		if latest_price:
			# Analyze multiple partial candles for stronger signals
			partial_candle_signal = analyze_partial_candles('EURUSD', timeframe=mt5.TIMEFRAME_M1, count=5)
			
			# Monitor real-time price movements as a confirmation layer
			tick_signal = monitor_real_time_price("EURUSD")
			
			if partial_candle_signal == "BUY" and tick_signal == "BUY":
				print(f"Confirmed Buy Signal at {latest_price.bid}")
			elif partial_candle_signal == "SELL" and tick_signal == "SELL":
				print(f"Confirmed Sell Signal at {latest_price.bid}")
			else:
				print(f"Signals do not align, holding off on trade decision.")
		
		time.sleep(1500)  # Adjust interval as needed


if not mt5.initialize(**data):
	print(f"Failed to connect to account #{data['login']}, error: {mt5.last_error()}")
	mt5.shutdown()
	exit()
else:
	print("Connected")
	get_balance_and_target()
	loop_through()
