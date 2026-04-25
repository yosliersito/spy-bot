print("\n=== SPY IRON CONDOR SCANNER (PRO FINAL) ===")

# =========================
# DATA
# =========================
spy = yf.Ticker("SPY")
hist = spy.history(period="1y")

price = hist["Close"].iloc[-1]
returns = hist["Close"].pct_change().dropna()

vol = returns.std() * np.sqrt(252)

# expected weekly move
weekly_move = price * (vol / np.sqrt(52))

upper = price + weekly_move
lower = price - weekly_move

# =========================
# OPTIONS CHAIN
# =========================
expiry = spy.options[0]
chain = spy.option_chain(expiry)

calls = chain.calls
puts = chain.puts

# =========================
# STRIKE SELECTION (ROBUST)
# =========================
def nearest(df, target):
    return df.iloc[(df["strike"] - target).abs().argsort()[:1]]["strike"].values[0]

# short strikes (sell premium near edges)
put_short = nearest(puts, lower)
call_short = nearest(calls, upper)

# long protection wings (defined risk)
put_long = nearest(puts, lower - weekly_move * 0.7)
call_long = nearest(calls, upper + weekly_move * 0.7)

# =========================
# EDGE MODEL
# =========================
position = (price - lower) / (upper - lower)

# volatility regime
if vol < 0.15:
    regime = "LOW VOL"
elif vol < 0.22:
    regime = "NORMAL VOL"
else:
    regime = "HIGH VOL"

# quality score (simple but institutional style)
score = 0

# mean reversion center bias
if 0.45 <= position <= 0.55:
    score += 40
elif 0.35 <= position <= 0.65:
    score += 25
else:
    score += 10

# volatility regime adjustment
if regime == "NORMAL VOL":
    score += 40
elif regime == "LOW VOL":
    score += 25
else:
    score += 10

# premium environment proxy
if weekly_move / price > 0.02:
    score += 20

# cap
score = min(score, 100)

# =========================
# OUTPUT
# =========================
print(f"Price: {price:.2f}")
print(f"Volatility: {vol:.4f}")
print(f"Regime: {regime}")

print("\n--- IRON CONDOR STRUCTURE ---")
print(f"PUT SELL : {put_short}")
print(f"PUT BUY  : {put_long}")
print(f"CALL SELL: {call_short}")
print(f"CALL BUY : {call_long}")

print("\n--- RISK ENGINE ---")
print(f"Expected Move: ±{weekly_move:.2f}")
print(f"Position Score: {score}/100")

if score >= 80:
    print("🟢 A+ SETUP (TRADEABLE)")
elif score >= 60:
    print("🟡 MARGINAL SETUP")
else:
    print("❌ NO TRADE")
