import yfinance as yf
import numpy as np

print("\n=== SPY IRON CONDOR SCANNER (PRO FULL SYSTEM) ===")

# =========================
# DATA
# =========================
spy = yf.Ticker("SPY")
hist = spy.history(period="1y")

price = hist["Close"].iloc[-1]
returns = hist["Close"].pct_change().dropna()

# Volatilidad anualizada
vol = returns.std() * np.sqrt(252)

# Expected move semanal
weekly_move = price * (vol / np.sqrt(52))

upper = price + weekly_move
lower = price - weekly_move

# =========================
# OPTIONS CHAIN
# =========================
expiry = spy.options[0]
chain = spy.option_chain(expiry)

calls = chain.calls.copy()
puts = chain.puts.copy()

# =========================
# FILTRO DE LIQUIDEZ (PRO)
# =========================
def filter_liquid(df):
    df = df.copy()
    df = df[(df["volume"] > 10) & (df["openInterest"] > 50)]
    return df

calls = filter_liquid(calls)
puts = filter_liquid(puts)

# fallback si se vacía
if len(calls) == 0:
    calls = spy.option_chain(expiry).calls
if len(puts) == 0:
    puts = spy.option_chain(expiry).puts

# =========================
# SELECCIÓN DE STRIKES (DELTA APPROX)
# =========================
def nearest(df, target):
    df = df.copy()
    return df.iloc[(df["strike"] - target).abs().argsort()[:1]]["strike"].values[0]

put_short = nearest(puts, lower)
call_short = nearest(calls, upper)

put_long = nearest(puts, lower - weekly_move * 0.7)
call_long = nearest(calls, upper + weekly_move * 0.7)

# =========================
# RÉGIMEN DE VOLATILIDAD
# =========================
if vol < 0.15:
    regime = "LOW VOL"
elif vol < 0.22:
    regime = "NORMAL VOL"
else:
    regime = "HIGH VOL"

# =========================
# PROBABILIDAD (APROX EDGE MODEL)
# =========================
position = (price - lower) / (upper - lower)

# probabilidad de éxito aproximada
if 0.45 <= position <= 0.55:
    prob = 0.70
elif 0.35 <= position <= 0.65:
    prob = 0.60
else:
    prob = 0.45

# ajuste por volatilidad
if regime == "NORMAL VOL":
    prob += 0.10
elif regime == "LOW VOL":
    prob += 0.05
else:
    prob -= 0.05

prob = min(max(prob, 0), 0.95)

# =========================
# EXPECTED VALUE (EDGE SIMPLIFICADO)
# =========================
credit_est = weekly_move * 0.3
risk_est = weekly_move * 0.7

ev = (prob * credit_est) - ((1 - prob) * risk_est)

# =========================
# SCORE FINAL
# =========================
score = int(prob * 100)

if ev > 0:
    score += 10

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

print("\n--- PRO METRICS ---")
print(f"Expected Move: ±{weekly_move:.2f}")
print(f"Win Probability: {prob*100:.1f}%")
print(f"Expected Value: {ev:.2f}")
print(f"Score: {score}/100")

# =========================
# DECISION
# =========================
if score >= 80 and ev > 0:
    print("🟢 A+ TRADE (HIGH EDGE)")
elif score >= 65:
    print("🟡 MARGINAL TRADE")
else:
    print("❌ NO TRADE")
