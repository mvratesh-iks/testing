"""
================================================================
  OPENING RANGE BREAKOUT (ORB) TRADING BOT
  Broker: Groww (Groww Trading API)
  Market: NSE (India)
================================================================

STRATEGY LOGIC:
  1. Wait for market to open (9:15 AM IST)
  2. Watch the first 15 minutes (9:15 - 9:30 AM) - this is the "opening range"
  3. Note the HIGH and LOW of this range for each stock in watchlist
  4. If price breaks ABOVE the opening range HIGH  -> BUY signal
  5. If price breaks BELOW the opening range LOW   -> SELL signal (or short)
  6. Set STOP LOSS at the opposite end of the range
  7. Exit all positions before market close (3:15 PM IST)

WHY THIS STRATEGY?
  - Simple, well-tested, works well at market open
  - Captures early momentum from overnight news/gaps
  - Has clear entry, exit, and stop-loss rules
================================================================
"""

import datetime
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

# FOR PAPER TRADING (FREE - no broker account needed):
#   pip install yfinance pandas
#
# FOR LIVE TRADING (paid Groww API subscription):
#   pip install growwapi pyotp pandas

import yfinance as yf  # Free market data for paper trading

# from growwapi import GrowwAPI  # Uncomment when going live
# import pyotp


# ================================================================
# CONFIGURATION - EDIT THESE VALUES
# ================================================================

CONFIG = {
    # === Broker credentials (get from https://groww.in/trade-api) ===
    # Steps to get these:
    #   1. Subscribe to Groww Trading API
    #   2. Go to Groww Cloud > API Keys page
    #   3. Click 'Generate TOTP token'
    #   4. Copy both the TOTP token and TOTP secret below
    "TOTP_TOKEN": "your_totp_token_here",
    "TOTP_SECRET": "your_totp_secret_here",

    # === Capital & Risk ===
    "TOTAL_CAPITAL": 10000,          # Start SMALL - Rs. 10,000
    "MAX_TRADES_PER_DAY": 3,          # Don't over-trade
    "RISK_PER_TRADE_PCT": 1.0,        # Risk only 1% of capital per trade
    "MAX_STOCKS_HELD": 2,             # Never hold more than 2 stocks at once

    # === Stocks to watch (curated for ORB - high liquidity + volatility) ===
    # Diversified across Energy, Auto, Banking, IT, Metals
    "WATCHLIST": [
        "RELIANCE",     # Energy/Conglomerate - massive liquidity, news-driven
        "TATAMOTORS",   # Auto - high intraday volatility, strong momentum
        "ICICIBANK",    # Banking - reactive to macro news
        "HDFCBANK",     # Banking - most liquid bank, tight spreads
        "INFY",         # IT - responds to global cues, gap opens common
        "TATASTEEL",    # Metals - volatile, great breakout candidate
        "ADANIENT",     # Diversified - high vol (small size only!)
    ],

    # === Timing (IST) ===
    "MARKET_OPEN": "09:15",
    "OPENING_RANGE_END": "09:30",     # First 15 min defines the range
    "SQUARE_OFF_TIME": "15:00",       # Exit all positions by 3:00 PM
    "MARKET_CLOSE": "15:30",

    # === Safety ===
    "PAPER_TRADING": True,            # !!! START WITH THIS = True !!!
    "MAX_LOSS_PER_DAY": 300,          # Stop bot if daily loss > Rs. 300
}


# ================================================================
# DATA CLASSES
# ================================================================

@dataclass
class OpeningRange:
    symbol: str
    high: float = 0.0
    low: float = float("inf")
    established: bool = False


@dataclass
class Position:
    symbol: str
    quantity: int
    entry_price: float
    stop_loss: float
    target: float
    side: str  # "BUY" or "SELL"
    entry_time: datetime.datetime


@dataclass
class BotState:
    opening_ranges: dict = field(default_factory=dict)
    positions: dict = field(default_factory=dict)
    trades_today: int = 0
    realised_pnl: float = 0.0
    is_active: bool = True


# ================================================================
# BROKER INTERFACE
# ================================================================

class BrokerInterface:
    """Wraps the Groww Trading API + a paper-trading fallback."""

    def __init__(self, config):
        self.config = config
        self.paper_mode = config["PAPER_TRADING"]
        self.groww = None

        if not self.paper_mode:
            # from growwapi import GrowwAPI
            # import pyotp
            # totp_gen = pyotp.TOTP(config["TOTP_SECRET"])
            # access_token = GrowwAPI.get_access_token(
            #     api_key=config["TOTP_TOKEN"],
            #     totp=totp_gen.now(),
            # )
            # self.groww = GrowwAPI(access_token)
            logging.info("Live trading mode ENABLED (Groww)")
        else:
            logging.info("Paper trading mode - no real orders will be placed")

    def get_ltp(self, symbol: str) -> float:
        """Get Last Traded Price for a symbol."""
        if self.paper_mode:
            # FREE: Use yfinance to get real NSE prices (~15 min delayed)
            # NSE symbols on Yahoo Finance need '.NS' suffix (e.g., RELIANCE.NS)
            try:
                ticker = yf.Ticker(f"{symbol}.NS")
                data = ticker.history(period="1d", interval="1m")
                if data.empty:
                    logging.warning(f"No data for {symbol}")
                    return 0.0
                return float(data["Close"].iloc[-1])
            except Exception as e:
                logging.error(f"yfinance error for {symbol}: {e}")
                return 0.0
        # response = self.groww.get_quote(
        #     exchange=self.groww.EXCHANGE_NSE,
        #     segment=self.groww.SEGMENT_CASH,
        #     trading_symbol=symbol,
        # )
        # return response["last_price"]

    def place_order(self, symbol: str, qty: int, side: str, price: float) -> str:
        """Place a market order. Returns order_id."""
        if self.paper_mode:
            order_id = f"PAPER-{int(time.time())}"
            logging.info(f"[PAPER] {side} {qty} {symbol} @ ~{price}")
            return order_id

        # response = self.groww.place_order(
        #     trading_symbol=symbol,
        #     quantity=qty,
        #     price=0,                                         # 0 for market order
        #     validity=self.groww.VALIDITY_DAY,
        #     exchange=self.groww.EXCHANGE_NSE,
        #     segment=self.groww.SEGMENT_CASH,
        #     product=self.groww.PRODUCT_MIS,                  # Intraday
        #     order_type=self.groww.ORDER_TYPE_MARKET,
        #     transaction_type=(self.groww.TRANSACTION_TYPE_BUY
        #                       if side == "BUY"
        #                       else self.groww.TRANSACTION_TYPE_SELL),
        # )
        # return response["groww_order_id"]

    def get_historical_range(self, symbol: str, start, end) -> tuple:
        """Fetch high/low between two timestamps for opening range."""
        if self.paper_mode:
            # FREE: Fetch real opening range from yfinance
            try:
                ticker = yf.Ticker(f"{symbol}.NS")
                data = ticker.history(period="1d", interval="1m")
                if data.empty:
                    return 0.0, 0.0
                # Get first 15 minutes of today's data (opening range)
                opening_bars = data.head(15)
                high = float(opening_bars["High"].max())
                low  = float(opening_bars["Low"].min())
                return high, low
            except Exception as e:
                logging.error(f"yfinance error for {symbol}: {e}")
                return 0.0, 0.0
        # In real usage: self.groww.get_historical_candle_data(...)
        return 0.0, 0.0


# ================================================================
# STRATEGY: OPENING RANGE BREAKOUT
# ================================================================

class ORBStrategy:
    def __init__(self, config, broker, state):
        self.config = config
        self.broker = broker
        self.state = state

    def establish_opening_range(self):
        """Called at 9:30 AM - captures the first 15 min high/low per stock."""
        today = datetime.datetime.now().replace(hour=9, minute=15, second=0)
        end   = datetime.datetime.now().replace(hour=9, minute=30, second=0)

        for symbol in self.config["WATCHLIST"]:
            high, low = self.broker.get_historical_range(symbol, today, end)
            self.state.opening_ranges[symbol] = OpeningRange(
                symbol=symbol, high=high, low=low, established=True
            )
            logging.info(f"OR for {symbol}: High={high}, Low={low}")

    def calculate_position_size(self, entry: float, stop_loss: float) -> int:
        """Position sizing based on risk-per-trade rule."""
        risk_amt = self.config["TOTAL_CAPITAL"] * self.config["RISK_PER_TRADE_PCT"] / 100
        risk_per_share = abs(entry - stop_loss)
        if risk_per_share == 0:
            return 0
        qty = int(risk_amt / risk_per_share)
        # Also cap by available capital
        max_qty_by_capital = int(self.config["TOTAL_CAPITAL"] / entry)
        return max(1, min(qty, max_qty_by_capital))

    def check_for_signals(self):
        """Called every minute after 9:30 AM."""
        if self._should_stop_trading():
            return

        for symbol, orb in self.state.opening_ranges.items():
            if not orb.established or symbol in self.state.positions:
                continue

            ltp = self.broker.get_ltp(symbol)

            # BUY signal: price breaks above opening high
            if ltp > orb.high:
                self._enter_trade(symbol, "BUY", ltp, stop_loss=orb.low)

            # SELL signal: price breaks below opening low
            elif ltp < orb.low:
                self._enter_trade(symbol, "SELL", ltp, stop_loss=orb.high)

    def _enter_trade(self, symbol: str, side: str, entry: float, stop_loss: float):
        if self.state.trades_today >= self.config["MAX_TRADES_PER_DAY"]:
            return
        if len(self.state.positions) >= self.config["MAX_STOCKS_HELD"]:
            return

        qty = self.calculate_position_size(entry, stop_loss)
        if qty <= 0:
            return

        # Target: 2x the risk (reward:risk = 2:1)
        risk = abs(entry - stop_loss)
        target = entry + 2 * risk if side == "BUY" else entry - 2 * risk

        order_id = self.broker.place_order(symbol, qty, side, entry)
        if order_id:
            self.state.positions[symbol] = Position(
                symbol=symbol, quantity=qty, entry_price=entry,
                stop_loss=stop_loss, target=target, side=side,
                entry_time=datetime.datetime.now(),
            )
            self.state.trades_today += 1
            logging.info(f"ENTERED: {side} {qty} {symbol} @ {entry} | SL={stop_loss} | Target={target}")

    def manage_open_positions(self):
        """Check open positions for stop-loss or target hits."""
        to_close = []
        for symbol, pos in self.state.positions.items():
            ltp = self.broker.get_ltp(symbol)

            hit_target = (pos.side == "BUY"  and ltp >= pos.target)  or \
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
        """Exit every open position (called before market close)."""
        for symbol, pos in list(self.state.positions.items()):
            ltp = self.broker.get_ltp(symbol)
            self._exit_trade(pos, ltp, "EOD-SQUAREOFF")
            del self.state.positions[symbol]

    def _exit_trade(self, pos: Position, exit_price: float, reason: str):
        opposite = "SELL" if pos.side == "BUY" else "BUY"
        self.broker.place_order(pos.symbol, pos.quantity, opposite, exit_price)
        pnl = (exit_price - pos.entry_price) * pos.quantity
        if pos.side == "SELL":
            pnl = -pnl
        self.state.realised_pnl += pnl
        logging.info(f"EXITED [{reason}]: {pos.symbol} @ {exit_price} | P&L: Rs.{pnl:.2f}")

    def _should_stop_trading(self):
        if self.state.realised_pnl <= -self.config["MAX_LOSS_PER_DAY"]:
            logging.warning("Max daily loss hit - stopping bot for the day.")
            self.state.is_active = False
            return True
        return False


# ================================================================
# MAIN BOT LOOP
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
    strategy = ORBStrategy(CONFIG, broker, state)

    logging.info("=" * 60)
    logging.info(f"BOT STARTED | Paper Trading: {CONFIG['PAPER_TRADING']}")
    logging.info(f"Capital: Rs.{CONFIG['TOTAL_CAPITAL']} | Watchlist: {CONFIG['WATCHLIST']}")
    logging.info("=" * 60)

    opening_range_done = False

    while state.is_active:
        current_time = now_hhmm()

        # Before market opens - wait
        if current_time < CONFIG["MARKET_OPEN"]:
            logging.info(f"Waiting for market open... ({current_time})")
            time.sleep(30)
            continue

        # After market close - stop
        if current_time >= CONFIG["MARKET_CLOSE"]:
            logging.info("Market closed. Bot shutting down.")
            break

        # Establish opening range at 9:30 AM
        if current_time >= CONFIG["OPENING_RANGE_END"] and not opening_range_done:
            strategy.establish_opening_range()
            opening_range_done = True

        # Square-off before close
        if current_time >= CONFIG["SQUARE_OFF_TIME"]:
            strategy.square_off_all()
            logging.info(f"Day complete. Total P&L: Rs.{state.realised_pnl:.2f}")
            break

        # Regular trading loop
        if opening_range_done:
            strategy.check_for_signals()
            strategy.manage_open_positions()

        time.sleep(60)  # Check every 1 minute


if __name__ == "__main__":
    run_bot()
