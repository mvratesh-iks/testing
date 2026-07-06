"""
================================================================
  BACKTESTER FOR THE ORB STRATEGY
================================================================
  Purpose: Test how the strategy WOULD have performed on past data
           before you risk any real money.

  Usage:
    Option A (RECOMMENDED - FREE, no signup):
      1. pip install yfinance pandas
      2. Just run: python backtest.py
         It will auto-download 60 days of data from Yahoo Finance
         for all watchlist stocks and backtest.

    Option B (Manual CSVs):
      Place your own CSVs in ./data/ folder (format: timestamp, open,
      high, low, close, volume) and set USE_YFINANCE = False below.

  What you'll see:
    - Win rate per stock
    - Average P&L per trade
    - Total return
    - Estimated net P&L after brokerage
================================================================
"""

import csv
import datetime
import os
from collections import defaultdict
from dataclasses import dataclass

# Free market data - pip install yfinance
import yfinance as yf


# ================================================================
# CONFIG - match your bot config
# ================================================================

USE_YFINANCE = True            # True = auto-download free data

# ⚠️  Yahoo Finance data limits (IMPORTANT):
#   - "1m"  interval → max 7 days of history
#   - "5m"  interval → max 60 days of history
#   - "15m" interval → max 60 days of history
#   - "1h"  interval → max 730 days of history
#
# For a meaningful backtest, we use 5-minute bars over 60 days.
# The opening range is calculated from the first 3 five-min bars
# (9:15, 9:20, 9:25) which covers 9:15-9:30 AM.

INTERVAL = "5m"                # "1m" for max resolution, "5m" for more history
LOOKBACK_DAYS = 60             # 7 max for 1m, 60 max for 5m

DATA_DIR = "./data"
STARTING_CAPITAL = 10000
RISK_PER_TRADE_PCT = 1.0
MAX_TRADES_PER_DAY = 3

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
    side: str          # BUY or SELL
    entry: float
    exit: float
    qty: int
    stop_loss: float
    target: float
    exit_reason: str   # TARGET, STOP-LOSS, EOD
    pnl: float

    def pnl_pct(self):
        return (self.pnl / (self.entry * self.qty)) * 100


# ================================================================
# LOAD HISTORICAL DATA
# ================================================================

def load_data(symbol: str) -> list:
    """Load 1-min OHLCV data. Uses yfinance if enabled, else reads CSV."""
    if USE_YFINANCE:
        return load_from_yfinance(symbol)

    filepath = os.path.join(DATA_DIR, f"{symbol}.csv")
    if not os.path.exists(filepath):
        print(f"  ⚠️  No data for {symbol} at {filepath}")
        return []

    rows = []
    with open(filepath) as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "timestamp": datetime.datetime.fromisoformat(row["timestamp"]),
                "open":  float(row["open"]),
                "high":  float(row["high"]),
                "low":   float(row["low"]),
                "close": float(row["close"]),
                "volume": int(row["volume"]),
            })
    return rows


def load_from_yfinance(symbol: str) -> list:
    """Download recent OHLCV data from Yahoo Finance (FREE)."""
    ticker = yf.Ticker(f"{symbol}.NS")   # .NS suffix = NSE
    try:
        df = ticker.history(period=f"{LOOKBACK_DAYS}d", interval=INTERVAL)
    except Exception as e:
        print(f"  ❌  yfinance error for {symbol}: {e}")
        return []

    if df.empty:
        print(f"  ❌  No data returned for {symbol}")
        print(f"      Tried: period={LOOKBACK_DAYS}d, interval={INTERVAL}")
        print(f"      Try: reduce LOOKBACK_DAYS or use a coarser INTERVAL")
        return []

    rows = []
    for ts, row in df.iterrows():
        rows.append({
            "timestamp": ts.to_pydatetime().replace(tzinfo=None),
            "open":  float(row["Open"]),
            "high":  float(row["High"]),
            "low":   float(row["Low"]),
            "close": float(row["Close"]),
            "volume": int(row["Volume"]) if row["Volume"] > 0 else 0,
        })
    # Show data range so user can verify it worked
    first = rows[0]["timestamp"].date()
    last  = rows[-1]["timestamp"].date()
    print(f"  📥 {symbol}: {len(rows)} bars ({INTERVAL}) from {first} to {last}")
    return rows


def group_by_day(rows: list) -> dict:
    """Group 1-min bars by trading day."""
    by_day = defaultdict(list)
    for r in rows:
        by_day[r["timestamp"].date()].append(r)
    return dict(by_day)


# ================================================================
# BACKTEST ONE STOCK, ONE DAY
# ================================================================

def backtest_day(symbol: str, day_bars: list, capital: float) -> Trade:
    """Simulate the ORB strategy for a single day."""
    # 1. Get opening range (9:15 - 9:30 AM)
    # Works with both 1m bars (15 bars) and 5m bars (3 bars)
    or_bars = [b for b in day_bars
               if datetime.time(9, 15) <= b["timestamp"].time() <= datetime.time(9, 30)]

    # Need at least 2 bars to establish a meaningful range
    if len(or_bars) < 2:
        return None

    or_high = max(b["high"] for b in or_bars)
    or_low  = min(b["low"]  for b in or_bars)

    # Skip if range is zero (data issue)
    if or_high <= or_low:
        return None

    # 2. Look for breakout AFTER opening range ends
    trading_bars = [b for b in day_bars if b["timestamp"].time() > datetime.time(9, 30)]

    entry, side, stop_loss, target = None, None, None, None

    for bar in trading_bars:
        # End of day - if still no trade, skip
        if bar["timestamp"].time() >= datetime.time(15, 0):
            break

        # Breakout ABOVE opening range - BUY
        if entry is None and bar["high"] > or_high:
            entry     = or_high  # Assume entry at breakout level
            side      = "BUY"
            stop_loss = or_low
            target    = entry + 2 * (entry - stop_loss)
            entry_bar = bar

        # Breakdown BELOW opening range - SELL
        elif entry is None and bar["low"] < or_low:
            entry     = or_low
            side      = "SELL"
            stop_loss = or_high
            target    = entry - 2 * (stop_loss - entry)
            entry_bar = bar

        # If in trade, check for target/stop
        if entry is not None and bar["timestamp"] > entry_bar["timestamp"]:
            if side == "BUY":
                if bar["low"] <= stop_loss:
                    return _close_trade(symbol, entry_bar, bar, entry, stop_loss, side, capital, or_low, or_high, target, "STOP-LOSS")
                if bar["high"] >= target:
                    return _close_trade(symbol, entry_bar, bar, entry, target, side, capital, or_low, or_high, target, "TARGET")
            else:  # SELL
                if bar["high"] >= stop_loss:
                    return _close_trade(symbol, entry_bar, bar, entry, stop_loss, side, capital, or_low, or_high, target, "STOP-LOSS")
                if bar["low"] <= target:
                    return _close_trade(symbol, entry_bar, bar, entry, target, side, capital, or_low, or_high, target, "TARGET")

    # Trade still open at 3 PM - square off at close
    if entry is not None:
        last_bar = trading_bars[-1]
        return _close_trade(symbol, entry_bar, last_bar, entry, last_bar["close"], side, capital, or_low, or_high, target, "EOD")

    return None


def _close_trade(symbol, entry_bar, exit_bar, entry, exit_price, side, capital, or_low, or_high, target, reason):
    risk_amt      = capital * RISK_PER_TRADE_PCT / 100
    risk_per_share = abs(entry - (or_low if side == "BUY" else or_high))
    qty = max(1, int(risk_amt / risk_per_share)) if risk_per_share else 1

    pnl = (exit_price - entry) * qty
    if side == "SELL":
        pnl = -pnl

    return Trade(
        date=entry_bar["timestamp"].date().isoformat(),
        symbol=symbol,
        side=side,
        entry=entry,
        exit=exit_price,
        qty=qty,
        stop_loss=or_low if side == "BUY" else or_high,
        target=target,
        exit_reason=reason,
        pnl=pnl,
    )


# ================================================================
# RUN THE BACKTEST
# ================================================================

def run_backtest():
    print("=" * 60)
    print("  BACKTESTING ORB STRATEGY")
    print(f"  Interval: {INTERVAL} | Lookback: {LOOKBACK_DAYS} days")
    print("=" * 60)

    all_trades = []
    capital = STARTING_CAPITAL
    total_days_processed = 0
    total_days_with_trades = 0

    for symbol in WATCHLIST:
        print(f"\n📊 {symbol}")
        rows = load_data(symbol)
        if not rows:
            continue

        by_day = group_by_day(rows)
        stock_trades = []
        days_no_signal = 0

        for day, bars in sorted(by_day.items()):
            total_days_processed += 1
            trade = backtest_day(symbol, bars, capital)
            if trade:
                stock_trades.append(trade)
                capital += trade.pnl
                total_days_with_trades += 1
            else:
                days_no_signal += 1

        # Per-stock stats
        if stock_trades:
            wins    = [t for t in stock_trades if t.pnl > 0]
            win_pct = len(wins) / len(stock_trades) * 100
            total   = sum(t.pnl for t in stock_trades)
            print(f"  ✅ {len(stock_trades)} trades across {len(by_day)} days")
            print(f"     Win rate: {win_pct:.1f}% | Total P&L: ₹{total:,.2f}")
            print(f"     Days with no signal: {days_no_signal}")
        else:
            print(f"  ⚠️  No trades — checked {len(by_day)} days, none had breakouts")

        all_trades.extend(stock_trades)

    # === OVERALL STATS ===
    print("\n" + "=" * 60)
    print("  OVERALL RESULTS")
    print("=" * 60)
    print(f"  Total stock-days scanned: {total_days_processed}")
    print(f"  Days with trades:         {total_days_with_trades}")

    if not all_trades:
        print("\n  ❌ NO TRADES EXECUTED")
        print("\n  Possible reasons:")
        print("  1. No data downloaded (check messages above)")
        print("  2. yfinance rate limit — wait 5 min and retry")
        print("  3. Interval + lookback mismatch:")
        print(f"     Currently: interval={INTERVAL}, lookback={LOOKBACK_DAYS} days")
        print("     Try: INTERVAL='1m' with LOOKBACK_DAYS=7")
        print("     Or:  INTERVAL='5m' with LOOKBACK_DAYS=60")
        print("  4. Genuinely no breakouts in this period (unusual)")
        return

    total_pnl  = sum(t.pnl for t in all_trades)
    wins       = [t for t in all_trades if t.pnl > 0]
    losses     = [t for t in all_trades if t.pnl <= 0]
    win_rate   = len(wins) / len(all_trades) * 100
    avg_win    = sum(t.pnl for t in wins)   / len(wins)   if wins   else 0
    avg_loss   = sum(t.pnl for t in losses) / len(losses) if losses else 0
    return_pct = (total_pnl / STARTING_CAPITAL) * 100

    print(f"  Total trades:      {len(all_trades)}")
    print(f"  Winners:           {len(wins)}  |  Losers: {len(losses)}")
    print(f"  Win rate:          {win_rate:.1f}%")
    print(f"  Avg win:           ₹{avg_win:,.2f}")
    print(f"  Avg loss:          ₹{avg_loss:,.2f}")
    print(f"  Total P&L:         ₹{total_pnl:,.2f}")
    print(f"  Return on capital: {return_pct:.2f}%")
    print(f"  Ending capital:    ₹{STARTING_CAPITAL + total_pnl:,.2f}")

    # === REALITY CHECK - brokerage ===
    # Zerodha/Groww: ~₹40 per round-trip intraday trade
    est_brokerage = len(all_trades) * 40
    print(f"\n  ⚠️  Estimated brokerage & taxes: ~₹{est_brokerage:,.2f}")
    print(f"  💰 Net P&L after costs: ~₹{total_pnl - est_brokerage:,.2f}")

    # === SAVE TRADES TO CSV FOR ANALYSIS ===
    with open("trades.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "symbol", "side", "entry", "exit", "qty",
                         "stop_loss", "target", "exit_reason", "pnl"])
        for t in all_trades:
            writer.writerow([t.date, t.symbol, t.side, t.entry, t.exit, t.qty,
                             t.stop_loss, t.target, t.exit_reason, t.pnl])
    print(f"\n  📄 Saved {len(all_trades)} trades to trades.csv")
    print(f"     Run: python analyze.py  to see detailed breakdown")


if __name__ == "__main__":
    run_backtest()
