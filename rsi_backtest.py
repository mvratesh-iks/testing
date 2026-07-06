"""
================================================================
  RSI MEAN-REVERSION STRATEGY BACKTEST
================================================================

  STRATEGY LOGIC:
    1. Calculate RSI(14) for each stock — a 0-100 momentum indicator
    2. If RSI drops BELOW 30 → stock is oversold → BUY (expect bounce)
    3. If RSI rises ABOVE 70 → stock is overbought → SELL (expect drop)
    4. Exit when RSI returns to neutral (crosses 50)
    5. Stop-loss if trade goes 1% against us

  WHY THIS MIGHT WORK WHERE ORB DIDN'T:
    - ORB failed because market wasn't trending strongly
    - RSI mean-reversion thrives EXACTLY in that environment
    - It's the natural complement to breakout strategies

  Usage:
    python rsi_backtest.py
================================================================
"""

import csv
import datetime
import os
from collections import defaultdict
from dataclasses import dataclass

import yfinance as yf


# ================================================================
# CONFIG
# ================================================================

INTERVAL = "5m"
LOOKBACK_DAYS = 60
STARTING_CAPITAL = 10000
RISK_PER_TRADE_PCT = 1.0

# RSI parameters
RSI_PERIOD          = 14      # Standard RSI period
RSI_OVERSOLD        = 30      # Buy when RSI drops below this
RSI_OVERBOUGHT      = 70      # Sell when RSI rises above this
RSI_EXIT            = 50      # Exit when RSI crosses neutral

# Risk controls
STOP_LOSS_PCT       = 1.0     # Exit if trade goes 1% against us
MAX_HOLD_BARS       = 20      # Exit after 20 bars (100 min) even if no signal
LAST_ENTRY_TIME     = "14:30" # Stop new entries 1hr before close

WATCHLIST = [
    "RELIANCE", "TATAMOTORS", "ICICIBANK",
    "HDFCBANK", "INFY", "TATASTEEL", "ADANIENT",
]


# ================================================================
# TRADE RECORD
# ================================================================

@dataclass
class Trade:
    date: str
    symbol: str
    side: str
    entry: float
    exit: float
    qty: int
    stop_loss: float
    exit_reason: str
    pnl: float
    rsi_at_entry: float


# ================================================================
# RSI CALCULATION
# ================================================================

def calculate_rsi(prices: list, period: int = 14) -> list:
    """
    Calculate RSI for a list of closing prices.
    Returns a list of RSI values (same length as input, with None for first `period` bars).
    """
    if len(prices) < period + 1:
        return [None] * len(prices)

    rsi_values = [None] * period
    gains = []
    losses = []

    # Initial average gain/loss
    for i in range(1, period + 1):
        change = prices[i] - prices[i - 1]
        gains.append(max(change, 0))
        losses.append(max(-change, 0))

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    if avg_loss == 0:
        rsi_values.append(100)
    else:
        rs = avg_gain / avg_loss
        rsi_values.append(100 - (100 / (1 + rs)))

    # Smoothed RSI for the rest (Wilder's smoothing)
    for i in range(period + 1, len(prices)):
        change = prices[i] - prices[i - 1]
        gain = max(change, 0)
        loss = max(-change, 0)

        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period

        if avg_loss == 0:
            rsi_values.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi_values.append(100 - (100 / (1 + rs)))

    return rsi_values


# ================================================================
# DATA LOADING
# ================================================================

def load_from_yfinance(symbol: str) -> list:
    ticker = yf.Ticker(f"{symbol}.NS")
    try:
        df = ticker.history(period=f"{LOOKBACK_DAYS}d", interval=INTERVAL)
    except Exception as e:
        print(f"  ❌  yfinance error for {symbol}: {e}")
        return []

    if df.empty:
        print(f"  ❌  No data returned for {symbol}")
        return []

    rows = []
    for ts, row in df.iterrows():
        rows.append({
            "timestamp": ts.to_pydatetime().replace(tzinfo=None),
            "open":  float(row["Open"]),
            "high":  float(row["High"]),
            "low":   float(row["Low"]),
            "close": float(row["Close"]),
        })

    first = rows[0]["timestamp"].date()
    last  = rows[-1]["timestamp"].date()
    print(f"  📥 {symbol}: {len(rows)} bars from {first} to {last}")
    return rows


# ================================================================
# BACKTEST LOGIC
# ================================================================

def backtest_symbol(symbol: str, bars: list, capital: float) -> list:
    """Run RSI strategy across all bars for one symbol. Returns list of Trades."""
    if len(bars) < RSI_PERIOD + 10:
        return []

    # Calculate RSI for all bars
    closes = [b["close"] for b in bars]
    rsi = calculate_rsi(closes, RSI_PERIOD)

    trades = []
    position = None  # dict with entry_price, side, entry_bar_idx, etc.

    cutoff_h, cutoff_m = map(int, LAST_ENTRY_TIME.split(":"))
    cutoff_time = datetime.time(cutoff_h, cutoff_m)

    for i, bar in enumerate(bars):
        current_rsi = rsi[i]
        if current_rsi is None:
            continue

        # === MANAGE OPEN POSITION ===
        if position is not None:
            bars_held = i - position["entry_idx"]
            entry = position["entry"]
            side = position["side"]

            # Stop-loss check
            if side == "BUY":
                loss_pct = (entry - bar["low"]) / entry * 100
                if loss_pct >= STOP_LOSS_PCT:
                    trades.append(_close_position(symbol, position, bar, entry * (1 - STOP_LOSS_PCT/100), "STOP-LOSS"))
                    position = None
                    continue
            else:
                loss_pct = (bar["high"] - entry) / entry * 100
                if loss_pct >= STOP_LOSS_PCT:
                    trades.append(_close_position(symbol, position, bar, entry * (1 + STOP_LOSS_PCT/100), "STOP-LOSS"))
                    position = None
                    continue

            # RSI reverted to neutral → exit
            if (side == "BUY" and current_rsi >= RSI_EXIT) or \
               (side == "SELL" and current_rsi <= RSI_EXIT):
                trades.append(_close_position(symbol, position, bar, bar["close"], "RSI-NEUTRAL"))
                position = None
                continue

            # Max hold time reached
            if bars_held >= MAX_HOLD_BARS:
                trades.append(_close_position(symbol, position, bar, bar["close"], "TIME-EXIT"))
                position = None
                continue

            # EOD square-off (3 PM)
            if bar["timestamp"].time() >= datetime.time(15, 0):
                trades.append(_close_position(symbol, position, bar, bar["close"], "EOD"))
                position = None
                continue

        # === LOOK FOR NEW ENTRY ===
        else:
            # Skip if past cutoff or too close to EOD
            if bar["timestamp"].time() >= cutoff_time:
                continue

            # Skip first 30 min of day (let market settle)
            if bar["timestamp"].time() < datetime.time(9, 45):
                continue

            # OVERSOLD → BUY
            if current_rsi < RSI_OVERSOLD:
                position = {
                    "entry": bar["close"],
                    "side": "BUY",
                    "entry_idx": i,
                    "entry_bar": bar,
                    "rsi": current_rsi,
                    "stop_loss": bar["close"] * (1 - STOP_LOSS_PCT/100),
                }

            # OVERBOUGHT → SELL
            elif current_rsi > RSI_OVERBOUGHT:
                position = {
                    "entry": bar["close"],
                    "side": "SELL",
                    "entry_idx": i,
                    "entry_bar": bar,
                    "rsi": current_rsi,
                    "stop_loss": bar["close"] * (1 + STOP_LOSS_PCT/100),
                }

    # Close any open position at end of data
    if position is not None:
        last_bar = bars[-1]
        trades.append(_close_position(symbol, position, last_bar, last_bar["close"], "END-OF-DATA"))

    return trades


def _close_position(symbol, position, exit_bar, exit_price, reason):
    entry = position["entry"]
    side = position["side"]

    # Position sizing
    risk_amt = STARTING_CAPITAL * RISK_PER_TRADE_PCT / 100
    risk_per_share = entry * (STOP_LOSS_PCT / 100)
    qty = max(1, int(risk_amt / risk_per_share))

    pnl = (exit_price - entry) * qty
    if side == "SELL":
        pnl = -pnl

    return Trade(
        date=position["entry_bar"]["timestamp"].date().isoformat(),
        symbol=symbol,
        side=side,
        entry=entry,
        exit=exit_price,
        qty=qty,
        stop_loss=position["stop_loss"],
        exit_reason=reason,
        pnl=pnl,
        rsi_at_entry=position["rsi"],
    )


# ================================================================
# MAIN
# ================================================================

def run_backtest():
    print("=" * 60)
    print(f"  RSI MEAN-REVERSION BACKTEST")
    print(f"  RSI({RSI_PERIOD}) | Oversold<{RSI_OVERSOLD} | Overbought>{RSI_OVERBOUGHT}")
    print(f"  Stop-loss: {STOP_LOSS_PCT}% | Exit at RSI={RSI_EXIT}")
    print("=" * 60)

    all_trades = []

    for symbol in WATCHLIST:
        print(f"\n📊 {symbol}")
        bars = load_from_yfinance(symbol)
        if not bars:
            continue

        stock_trades = backtest_symbol(symbol, bars, STARTING_CAPITAL)

        if stock_trades:
            wins = [t for t in stock_trades if t.pnl > 0]
            win_pct = len(wins) / len(stock_trades) * 100
            total = sum(t.pnl for t in stock_trades)
            marker = "✅" if total > 0 else "❌"
            print(f"  {marker} {len(stock_trades)} trades | Win: {win_pct:.1f}% | P&L: ₹{total:+,.0f}")
        else:
            print(f"  ⚠️  No trades")

        all_trades.extend(stock_trades)

    # === OVERALL ===
    print("\n" + "=" * 60)
    print("  OVERALL RESULTS")
    print("=" * 60)

    if not all_trades:
        print("  ❌ No trades executed. Try adjusting RSI thresholds.")
        return

    total_pnl = sum(t.pnl for t in all_trades)
    wins = [t for t in all_trades if t.pnl > 0]
    losses = [t for t in all_trades if t.pnl <= 0]
    win_rate = len(wins) / len(all_trades) * 100
    avg_win = sum(t.pnl for t in wins) / len(wins) if wins else 0
    avg_loss = sum(t.pnl for t in losses) / len(losses) if losses else 0

    print(f"  Total trades:       {len(all_trades)}  ({len(all_trades)/60:.1f}/day avg)")
    print(f"  Winners:            {len(wins)}  |  Losers: {len(losses)}")
    print(f"  Win rate:           {win_rate:.1f}%")
    print(f"  Avg win:            ₹{avg_win:+,.2f}")
    print(f"  Avg loss:           ₹{avg_loss:+,.2f}")
    print(f"  Gross P&L:          ₹{total_pnl:+,.2f}")

    est_brokerage = len(all_trades) * 40
    net_pnl = total_pnl - est_brokerage
    print(f"\n  Estimated brokerage: ~₹{est_brokerage:,.2f}")
    print(f"  💰 NET P&L after costs: ₹{net_pnl:+,.2f}")

    # Save trades
    with open("trades.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "symbol", "side", "entry", "exit", "qty",
                         "stop_loss", "target", "exit_reason", "pnl"])
        for t in all_trades:
            writer.writerow([t.date, t.symbol, t.side, t.entry, t.exit, t.qty,
                             t.stop_loss, "N/A", t.exit_reason, t.pnl])
    print(f"\n  📄 Saved {len(all_trades)} trades to trades.csv")
    print(f"     Run: python analyze.py  to see detailed breakdown")

    # Verdict
    print("\n" + "=" * 60)
    if net_pnl > 500:
        print("  ✅ PROMISING! RSI edge exists. Run analyze.py, then paper trade.")
    elif net_pnl > -1000:
        print("  ⚠️  Roughly breakeven. Could tune parameters or move on.")
    else:
        print("  ❌ Not profitable. Time to accept and go with Option 4.")
    print("=" * 60)


if __name__ == "__main__":
    run_backtest()
