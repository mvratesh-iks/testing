"""
================================================================
  ORB CONFLUENCE BOT v3
  Broker: Groww (Groww Trading API)
  Market: NSE (India)
================================================================

STRATEGY: Opening Range Breakout + 3 Confluence Filters

  STEP 1 — Opening Range (9:15-9:30 AM)
    Record high/low of first 15 min for each stock

  STEP 2 — Confluence Check (all 3 must pass to enter)
    Filter A: NIFTY DIRECTION
      - Only BUY if Nifty50 is GREEN (above yesterday's close)
      - Only SELL if Nifty50 is RED (below yesterday's close)
      - Stops fighting the broader market

    Filter B: VOLUME CONFIRMATION
      - Breakout bar volume must be > 1.5x the average bar volume
      - Ensures real buyers/sellers behind the move, not noise

    Filter C: RSI CONFIRMATION
      - Only BUY if RSI is between 40-65 (momentum building, not overbought)
      - Only SELL if RSI is between 35-60 (momentum falling, not oversold)
      - Avoids entering when stock already exhausted

  STEP 3 — Entry
    - Price must break beyond range by MIN_BREAKOUT_PCT (0.20%)
    - All 3 filters must be GREEN
    - Max 2 trades per day, max 2 stocks held at once

  STEP 4 — Exit
    - Target: 1.0x risk (realistic based on 11 days of data)
    - Stop-loss: opposite end of opening range
    - Hard exit at 3:00 PM regardless

WHAT CHANGED FROM v2:
  - Added Nifty direction filter (fixes losing BUY trades)
  - Added volume confirmation (fixes false breakouts)
  - Added RSI filter (avoids exhausted moves)
  - Target reduced from 1.5x to 1.0x (only 1/28 trades hit 1.5x!)
  - Removed AXISBANK + ADANIENT (biggest losers in 11-day data)
  - Reduced MAX_TRADES_PER_DAY from 3 to 2 (less brokerage)
================================================================
"""

import datetime
import logging
import time
import csv
import os
from dataclasses import dataclass, field
from typing import Optional

# FOR PAPER TRADING (FREE):
#   pip install yfinance pandas
# FOR LIVE TRADING:
#   pip install growwapi pyotp pandas

import yfinance as yf
import pandas as pd

# from growwapi import GrowwAPI
# import pyotp


# ================================================================
# CONFIGURATION
# ================================================================

CONFIG = {
    # === Broker credentials ===
    "TOTP_TOKEN": "your_totp_token_here",
    "TOTP_SECRET": "your_totp_secret_here",

    # === Capital & Risk ===
    "TOTAL_CAPITAL":      10000,
    "RISK_PER_TRADE_PCT": 1.0,
    "MAX_TRADES_PER_DAY": 2,       # Reduced from 3 — less brokerage
    "MAX_STOCKS_HELD":    2,
    "MAX_LOSS_PER_DAY":   300,

    # === ORB Filters (v2 — unchanged) ===
    "MIN_BREAKOUT_PCT":  0.20,     # Price must break range by 0.20%
    "MIN_RANGE_PCT":     0.50,     # Opening range must be >= 0.50% wide
    "LAST_ENTRY_TIME":   "12:00",  # No new trades after noon
    "TARGET_MULTIPLIER": 1.0,      # Changed from 1.5 → 1.0 (realistic!)

    # === NEW: Confluence Filters (v3) ===
    "USE_NIFTY_FILTER":   True,    # Only trade WITH the market direction
    "USE_VOLUME_FILTER":  True,    # Require 1.5x volume at breakout
    "VOLUME_MULTIPLIER":  1.5,     # How much above average volume needed
    "USE_RSI_FILTER":     True,    # RSI must be in healthy range
    "RSI_BUY_MIN":        40,      # RSI must be above this to BUY
    "RSI_BUY_MAX":        65,      # RSI must be below this to BUY
    "RSI_SELL_MIN":       35,      # RSI must be above this to SELL
    "RSI_SELL_MAX":       60,      # RSI must be below this to SELL
    "RSI_PERIOD":         14,      # Standard RSI period

    # === Watchlist (cleaned based on 11-day performance) ===
    # Removed: AXISBANK (-₹151), ADANIENT (-₹116), JSWSTEEL (-₹71)
    # Kept:    TCS (+₹131), TMPV (+₹72), SBIN (+₹16)
    "WATCHLIST": [
        # Auto
        "TMPV",        # TMPV.NS  ✅ Best performer in paper trading
        "TMCV",        # TMCV.NS  ✅
        "MARUTI",      # MARUTI.NS ✅
        "BAJAJ-AUTO",  # BAJAJ-AUTO.NS ✅

        # Banking
        "ICICIBANK",   # ICICIBANK.NS ✅
        "HDFCBANK",    # HDFCBANK.NS ✅
        "KOTAKBANK",   # KOTAKBANK.NS ✅
        "SBIN",        # SBIN.NS ✅ Positive in paper trading

        # IT
        "INFY",        # INFY.NS ✅
        "TCS",         # TCS.NS ✅ Best performer — only TARGET hit
        "WIPRO",       # WIPRO.NS ✅

        # Energy
        "RELIANCE",    # RELIANCE.NS ✅

        # Pharma
        "SUNPHARMA",   # SUNPHARMA.NS ✅
        "DRREDDY",     # DRREDDY.NS ✅
    ],

    # === Timing (IST) ===
    "MARKET_OPEN":       "09:15",
    "OPENING_RANGE_END": "09:30",
    "SQUARE_OFF_TIME":   "15:00",
    "MARKET_CLOSE":      "15:30",

    # === Mode ===
    "PAPER_TRADING": True,   # Keep True until consistently profitable!
}


# ================================================================
# DATA CLASSES
# ================================================================

@dataclass
class OpeningRange:
    symbol: str
    high: float = 0.0
    low: float = float("inf")
    avg_volume: float = 0.0    # NEW: average bar volume during opening range
    established: bool = False


@dataclass
class Position:
    symbol: str
    quantity: int
    entry_price: float
    stop_loss: float
    target: float
    side: str
    entry_time: datetime.datetime
    filters_passed: str = ""   # NEW: log which filters confirmed the trade


@dataclass
class BotState:
    opening_ranges: dict = field(default_factory=dict)
    positions: dict = field(default_factory=dict)
    closed_trades: list = field(default_factory=list)
    trades_today: int = 0
    realised_pnl: float = 0.0
    is_active: bool = True
    nifty_bias: str = "NEUTRAL"   # NEW: "BULLISH", "BEARISH", or "NEUTRAL"


# ================================================================
# BROKER / DATA INTERFACE
# ================================================================

class BrokerInterface:

    def __init__(self, config):
        self.config = config
        self.paper_mode = config["PAPER_TRADING"]
        self.groww = None

        self.yahoo_map = {
            "BAJAJ-AUTO": "BAJAJ-AUTO.NS",
            "DRREDDY":    "DRREDDY.NS",
            "KOTAKBANK":  "KOTAKBANK.NS",
            "MARUTI":     "MARUTI.NS",
            "SBIN":       "SBIN.NS",
            "SUNPHARMA":  "SUNPHARMA.NS",
            "WIPRO":      "WIPRO.NS",
            "ICICIBANK":  "ICICIBANK.NS",
            "HDFCBANK":   "HDFCBANK.NS",
            "TCS":        "TCS.NS",
            "TMPV":       "TMPV.NS",
            "TMCV":       "TMCV.NS",
            "RELIANCE":   "RELIANCE.NS",
            "INFY":       "INFY.NS",
        }

        if not self.paper_mode:
            logging.info("Live trading mode ENABLED (Groww)")
        else:
            logging.info("Paper trading mode - no real orders will be placed")

    def _yahoo_ticker(self, symbol: str) -> str:
        return self.yahoo_map.get(symbol, f"{symbol}.NS")

    def get_ltp(self, symbol: str) -> float:
        """Get Last Traded Price."""
        if self.paper_mode:
            try:
                ticker = yf.Ticker(self._yahoo_ticker(symbol))
                data = ticker.history(period="1d", interval="1m")
                if data.empty:
                    return 0.0
                return float(data["Close"].iloc[-1])
            except Exception as e:
                logging.error(f"yfinance error for {symbol}: {e}")
                return 0.0

    def get_todays_bars(self, symbol: str) -> pd.DataFrame:
        """Get all 1-min bars for today. Used for RSI + volume."""
        try:
            ticker = yf.Ticker(self._yahoo_ticker(symbol))
            data = ticker.history(period="1d", interval="1m")
            return data if not data.empty else pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    def get_nifty_bias(self) -> str:
        """
        Check if Nifty50 is bullish or bearish today.
        Bullish = current price above yesterday's close
        Bearish = current price below yesterday's close
        """
        try:
            ticker = yf.Ticker("^NSEI")   # Nifty50 Yahoo ticker
            data = ticker.history(period="2d", interval="1d")
            if len(data) < 2:
                return "NEUTRAL"
            prev_close = float(data["Close"].iloc[-2])
            curr_price = float(data["Close"].iloc[-1])
            if curr_price > prev_close * 1.001:    # 0.1% buffer
                return "BULLISH"
            elif curr_price < prev_close * 0.999:
                return "BEARISH"
            return "NEUTRAL"
        except Exception as e:
            logging.error(f"Nifty fetch error: {e}")
            return "NEUTRAL"

    def get_historical_range(self, symbol: str, start, end) -> tuple:
        """Fetch opening range high/low + avg volume."""
        if self.paper_mode:
            try:
                ticker = yf.Ticker(self._yahoo_ticker(symbol))
                data = ticker.history(period="1d", interval="1m")
                if data.empty:
                    return 0.0, 0.0, 0.0
                opening_bars = data.head(15)
                high = float(opening_bars["High"].max())
                low  = float(opening_bars["Low"].min())
                avg_vol = float(opening_bars["Volume"].mean())
                return high, low, avg_vol
            except Exception as e:
                logging.error(f"yfinance error for {symbol}: {e}")
                return 0.0, 0.0, 0.0
        return 0.0, 0.0, 0.0

    def place_order(self, symbol: str, qty: int, side: str, price: float) -> str:
        if self.paper_mode:
            order_id = f"PAPER-{int(time.time())}"
            logging.info(f"[PAPER] {side} {qty} {symbol} @ ~{price}")
            return order_id


# ================================================================
# RSI CALCULATION
# ================================================================

def calculate_rsi(prices: list, period: int = 14) -> float:
    """Calculate current RSI from a list of closing prices."""
    if len(prices) < period + 1:
        return 50.0  # neutral fallback

    gains, losses = [], []
    for i in range(1, period + 1):
        change = prices[i] - prices[i - 1]
        gains.append(max(change, 0))
        losses.append(max(-change, 0))

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    for i in range(period + 1, len(prices)):
        change = prices[i] - prices[i - 1]
        avg_gain = (avg_gain * (period - 1) + max(change, 0)) / period
        avg_loss = (avg_loss * (period - 1) + max(-change, 0)) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


# ================================================================
# CONFLUENCE STRATEGY
# ================================================================

class ConfluenceORBStrategy:

    def __init__(self, config, broker, state):
        self.config = config
        self.broker = broker
        self.state = state

    def check_nifty_bias(self):
        """Called once at market open — set today's market direction."""
        bias = self.broker.get_nifty_bias()
        self.state.nifty_bias = bias
        emoji = "📈" if bias == "BULLISH" else ("📉" if bias == "BEARISH" else "➡️")
        logging.info(f"Nifty bias today: {bias} {emoji}")
        if bias == "NEUTRAL":
            logging.info("Nifty neutral — will allow both BUY and SELL signals")

    def establish_opening_range(self):
        """Called at 9:30 AM."""
        today = datetime.datetime.now().replace(hour=9, minute=15, second=0)
        end   = datetime.datetime.now().replace(hour=9, minute=30, second=0)

        failed = []
        for symbol in self.config["WATCHLIST"]:
            high, low, avg_vol = self.broker.get_historical_range(symbol, today, end)
            if high == 0.0 or low == 0.0:
                failed.append(symbol)
                continue
            self.state.opening_ranges[symbol] = OpeningRange(
                symbol=symbol, high=high, low=low,
                avg_volume=avg_vol, established=True
            )
            range_pct = (high - low) / low * 100
            logging.info(f"OR {symbol}: H={high:.2f} L={low:.2f} "
                        f"Range={range_pct:.2f}% AvgVol={avg_vol:.0f}")

        if failed:
            logging.warning(f"No data (skipped): {failed}")

    def _check_confluence_filters(self, symbol: str, side: str,
                                   current_volume: float) -> tuple:
        """
        Run all 3 confluence filters.
        Returns (passed: bool, reason: str)
        """
        orb = self.state.opening_ranges[symbol]
        filters_passed = []
        filters_failed = []

        # === FILTER A: NIFTY DIRECTION ===
        if self.config["USE_NIFTY_FILTER"]:
            bias = self.state.nifty_bias
            if bias == "BULLISH" and side == "SELL":
                filters_failed.append(f"Nifty={bias} conflicts with SELL")
            elif bias == "BEARISH" and side == "BUY":
                filters_failed.append(f"Nifty={bias} conflicts with BUY")
            else:
                filters_passed.append(f"Nifty={bias}✅")

        # === FILTER B: VOLUME CONFIRMATION ===
        if self.config["USE_VOLUME_FILTER"] and orb.avg_volume > 0:
            vol_multiplier = self.config["VOLUME_MULTIPLIER"]
            required_vol = orb.avg_volume * vol_multiplier
            if current_volume >= required_vol:
                filters_passed.append(f"Vol={current_volume:.0f}✅")
            else:
                filters_failed.append(
                    f"Vol={current_volume:.0f} < {required_vol:.0f} needed"
                )

        # === FILTER C: RSI CONFIRMATION ===
        if self.config["USE_RSI_FILTER"]:
            bars = self.broker.get_todays_bars(symbol)
            if not bars.empty:
                closes = list(bars["Close"])
                rsi = calculate_rsi(closes, self.config["RSI_PERIOD"])
                if side == "BUY":
                    min_r = self.config["RSI_BUY_MIN"]
                    max_r = self.config["RSI_BUY_MAX"]
                    if min_r <= rsi <= max_r:
                        filters_passed.append(f"RSI={rsi}✅")
                    else:
                        filters_failed.append(
                            f"RSI={rsi} outside BUY range {min_r}-{max_r}"
                        )
                else:  # SELL
                    min_r = self.config["RSI_SELL_MIN"]
                    max_r = self.config["RSI_SELL_MAX"]
                    if min_r <= rsi <= max_r:
                        filters_passed.append(f"RSI={rsi}✅")
                    else:
                        filters_failed.append(
                            f"RSI={rsi} outside SELL range {min_r}-{max_r}"
                        )

        if filters_failed:
            return False, " | ".join(filters_failed)
        return True, " | ".join(filters_passed)

    def calculate_position_size(self, entry: float, stop_loss: float) -> int:
        risk_amt = self.config["TOTAL_CAPITAL"] * self.config["RISK_PER_TRADE_PCT"] / 100
        risk_per_share = abs(entry - stop_loss)
        if risk_per_share == 0:
            return 0
        qty = int(risk_amt / risk_per_share)
        max_by_capital = int(self.config["TOTAL_CAPITAL"] / entry)
        return max(1, min(qty, max_by_capital))

    def check_for_signals(self):
        """Called every minute — check each stock for confluence entry."""
        if self._should_stop_trading():
            return

        current_time = datetime.datetime.now().strftime("%H:%M")
        if current_time >= self.config["LAST_ENTRY_TIME"]:
            return

        for symbol, orb in self.state.opening_ranges.items():
            if not orb.established or symbol in self.state.positions:
                continue

            # Range filter
            min_range = self.config.get("MIN_RANGE_PCT", 0)
            if orb.low > 0:
                range_pct = (orb.high - orb.low) / orb.low * 100
                if range_pct < min_range:
                    continue

            ltp = self.broker.get_ltp(symbol)
            if ltp == 0.0:
                continue

            # Breakout trigger levels with buffer
            buf = self.config["MIN_BREAKOUT_PCT"] / 100
            buy_trigger  = orb.high * (1 + buf)
            sell_trigger = orb.low  * (1 - buf)

            # Get current bar volume (approximate from last bar)
            try:
                bars = self.broker.get_todays_bars(symbol)
                current_vol = float(bars["Volume"].iloc[-1]) if not bars.empty else 0
            except Exception:
                current_vol = 0

            # Check BUY signal
            if ltp > buy_trigger:
                passed, reason = self._check_confluence_filters(
                    symbol, "BUY", current_vol
                )
                if passed:
                    self._enter_trade(symbol, "BUY", ltp, orb.low, reason)
                else:
                    logging.info(f"SKIP BUY {symbol}: {reason}")

            # Check SELL signal
            elif ltp < sell_trigger:
                passed, reason = self._check_confluence_filters(
                    symbol, "SELL", current_vol
                )
                if passed:
                    self._enter_trade(symbol, "SELL", ltp, orb.high, reason)
                else:
                    logging.info(f"SKIP SELL {symbol}: {reason}")

    def _enter_trade(self, symbol: str, side: str, entry: float,
                     stop_loss: float, filters: str):
        if self.state.trades_today >= self.config["MAX_TRADES_PER_DAY"]:
            return
        if len(self.state.positions) >= self.config["MAX_STOCKS_HELD"]:
            return

        qty = self.calculate_position_size(entry, stop_loss)
        if qty <= 0:
            return

        risk = abs(entry - stop_loss)
        mult = self.config["TARGET_MULTIPLIER"]
        target = entry + mult * risk if side == "BUY" else entry - mult * risk

        order_id = self.broker.place_order(symbol, qty, side, entry)
        if order_id:
            self.state.positions[symbol] = Position(
                symbol=symbol, quantity=qty, entry_price=entry,
                stop_loss=stop_loss, target=target, side=side,
                entry_time=datetime.datetime.now(),
                filters_passed=filters,
            )
            self.state.trades_today += 1
            logging.info(
                f"ENTERED: {side} {qty} {symbol} @ {entry:.2f} | "
                f"SL={stop_loss:.2f} | Target={target:.2f} | "
                f"Filters: [{filters}]"
            )

    def manage_open_positions(self):
        """Check stop-loss and target every minute."""
        to_close = []
        for symbol, pos in self.state.positions.items():
            ltp = self.broker.get_ltp(symbol)
            if ltp == 0.0:
                logging.warning(f"Skipping {symbol} position check — no price")
                continue

            hit_target = (pos.side == "BUY"  and ltp >= pos.target) or \
                         (pos.side == "SELL" and ltp <= pos.target)
            hit_stop   = (pos.side == "BUY"  and ltp <= pos.stop_loss) or \
                         (pos.side == "SELL" and ltp >= pos.stop_loss)

            if hit_target or hit_stop:
                reason = "TARGET" if hit_target else "STOP-LOSS"
                self._exit_trade(pos, ltp, reason)
                to_close.append(symbol)

        for symbol in to_close:
            del self.state.positions[symbol]

    def square_off_all(self):
        """Exit everything at 3:00 PM."""
        for symbol, pos in list(self.state.positions.items()):
            ltp = self.broker.get_ltp(symbol)
            if ltp == 0.0:
                ltp = pos.entry_price  # fallback
            self._exit_trade(pos, ltp, "EOD-SQUAREOFF")
            del self.state.positions[symbol]

    def _exit_trade(self, pos: Position, exit_price: float, reason: str):
        opposite = "SELL" if pos.side == "BUY" else "BUY"
        self.broker.place_order(pos.symbol, pos.quantity, opposite, exit_price)
        pnl = (exit_price - pos.entry_price) * pos.quantity
        if pos.side == "SELL":
            pnl = -pnl
        self.state.realised_pnl += pnl
        self.state.closed_trades.append({
            "symbol":   pos.symbol,
            "side":     pos.side,
            "entry":    pos.entry_price,
            "exit":     exit_price,
            "stop_loss":pos.stop_loss,
            "target":   pos.target,
            "qty":      pos.quantity,
            "pnl":      round(pnl, 2),
            "reason":   reason,
            "filters":  pos.filters_passed,
        })
        logging.info(
            f"EXITED [{reason}]: {pos.symbol} @ {exit_price:.2f} | "
            f"P&L: Rs.{pnl:.2f}"
        )

    def _should_stop_trading(self):
        if self.state.realised_pnl <= -self.config["MAX_LOSS_PER_DAY"]:
            logging.warning("Max daily loss hit — stopping for the day.")
            self.state.is_active = False
            return True
        return False


# ================================================================
# DAILY REPORT
# ================================================================

def save_daily_report(state, config):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    os.makedirs("daily_logs", exist_ok=True)

    txt_path = f"daily_logs/{today}_report.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write(f"  PAPER TRADING DAILY REPORT — {today}\n")
        f.write("=" * 60 + "\n\n")

        f.write(f"  Bot version:     ORB Confluence v3\n")
        f.write(f"  Nifty bias:      {state.nifty_bias}\n")
        f.write(f"  Capital:         Rs.{config['TOTAL_CAPITAL']:,}\n")
        f.write(f"  Trades today:    {state.trades_today}\n")
        f.write(f"  Gross P&L:       Rs.{state.realised_pnl:+,.2f}\n")
        est_brokerage = state.trades_today * 40
        net = state.realised_pnl - est_brokerage
        f.write(f"  Est. brokerage:  Rs.{est_brokerage:,.2f}\n")
        f.write(f"  NET P&L:         Rs.{net:+,.2f}\n")
        verdict = "PROFITABLE" if net > 0 else ("BREAKEVEN" if net > -200 else "LOSS DAY")
        f.write(f"  Verdict:         {verdict}\n\n")

        f.write("-" * 60 + "\n")
        f.write("  OPENING RANGES\n")
        f.write("-" * 60 + "\n")
        f.write(f"  {'Stock':<12} {'OR High':>9} {'OR Low':>9} "
                f"{'Range%':>8} {'AvgVol':>10}\n")
        for symbol, orb in state.opening_ranges.items():
            if orb.high > 0:
                rng = (orb.high - orb.low) / orb.low * 100
                f.write(f"  {symbol:<12} {orb.high:>9.2f} {orb.low:>9.2f} "
                        f"{rng:>7.2f}% {orb.avg_volume:>10.0f}\n")
            else:
                f.write(f"  {symbol:<12} No data\n")

        f.write("\n" + "-" * 60 + "\n")
        f.write("  TRADES EXECUTED\n")
        f.write("-" * 60 + "\n")

        if not state.closed_trades:
            f.write("  No trades executed today.\n")
            f.write("  (All signals filtered out by confluence rules)\n")
        else:
            f.write(f"  {'Stock':<10} {'Side':<5} {'Entry':>8} {'Exit':>8} "
                    f"{'P&L':>8} {'Reason':<14} Filters\n")
            f.write(f"  {'-'*10} {'-'*5} {'-'*8} {'-'*8} "
                    f"{'-'*8} {'-'*14} {'-'*20}\n")
            for t in state.closed_trades:
                f.write(f"  {t['symbol']:<10} {t['side']:<5} {t['entry']:>8.2f} "
                        f"{t['exit']:>8.2f} {t['pnl']:>+8.2f} "
                        f"{t['reason']:<14} {t['filters']}\n")

        f.write("\n" + "=" * 60 + "\n")

    # Running CSV summary
    csv_path = "daily_logs/all_days_summary.csv"
    file_exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["date", "version", "nifty_bias", "trades",
                             "gross_pnl", "brokerage", "net_pnl"])
        writer.writerow([today, "v3", state.nifty_bias, state.trades_today,
                         round(state.realised_pnl, 2), est_brokerage,
                         round(net, 2)])

    logging.info(f"Report saved → daily_logs/{today}_report.txt")


# ================================================================
# MAIN LOOP
# ================================================================

def now_hhmm() -> str:
    return datetime.datetime.now().strftime("%H:%M")


def run_bot():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    broker   = BrokerInterface(CONFIG)
    state    = BotState()
    strategy = ConfluenceORBStrategy(CONFIG, broker, state)

    logging.info("=" * 60)
    logging.info(f"ORB CONFLUENCE BOT v3 | Paper: {CONFIG['PAPER_TRADING']}")
    logging.info(f"Capital: Rs.{CONFIG['TOTAL_CAPITAL']} | "
                 f"Stocks: {len(CONFIG['WATCHLIST'])}")
    logging.info(f"Filters: Nifty={CONFIG['USE_NIFTY_FILTER']} | "
                 f"Volume={CONFIG['USE_VOLUME_FILTER']} | "
                 f"RSI={CONFIG['USE_RSI_FILTER']}")
    logging.info("=" * 60)

    opening_range_done = False
    nifty_checked = False

    while state.is_active:
        current_time = now_hhmm()

        # Wait for market
        if current_time < CONFIG["MARKET_OPEN"]:
            logging.info(f"Waiting for market open... ({current_time})")
            time.sleep(30)
            continue

        # Market closed
        if current_time >= CONFIG["MARKET_CLOSE"]:
            logging.info("Market closed.")
            break

        # Check Nifty direction once at open
        if not nifty_checked:
            strategy.check_nifty_bias()
            nifty_checked = True

        # Establish opening range at 9:30
        if current_time >= CONFIG["OPENING_RANGE_END"] and not opening_range_done:
            strategy.establish_opening_range()
            opening_range_done = True

        # Square off before close
        if current_time >= CONFIG["SQUARE_OFF_TIME"]:
            strategy.square_off_all()
            logging.info(f"Day done. P&L: Rs.{state.realised_pnl:.2f}")
            break

        # Main trading loop
        if opening_range_done:
            strategy.check_for_signals()
            strategy.manage_open_positions()

        time.sleep(60)

    save_daily_report(state, CONFIG)
    logging.info("Bot shut down. Check daily_logs/ for today's report.")


if __name__ == "__main__":
    run_bot()
