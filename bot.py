import yfinance as yf
import numpy as np

spy = yf.Ticker("SPY")
hist = spy.history(period="1y")

price = hist["Close"].iloc[-1]
returns = hist["Close"].pct_change().dropna()

vol = returns.std() * np.sqrt(252)
weekly_move = price * (vol / np.sqrt(52))

support = price - weekly_move
resistance = price + weekly_move

print("SPY WEEKLY REPORT")
print("------------------")
print(f"Price: {price:.2f}")
print(f"Support: {support:.2f}")
print(f"Resistance: {resistance:.2f}")

if support < price < resistance:
    print("🟢 GOOD ZONE FOR IRON CONDOR")
else:
    print("❌ BAD ZONE")
