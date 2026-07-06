# 📌 Things To Do — Maddy

> **Follow these steps in order after unzipping the folder.**

---

## Step 1: Install Python (skip if already installed)

- Download from [python.org/downloads](https://python.org/downloads)
- Pick Python **3.9 or later**
- During install → ✅ **check "Add Python to PATH"** (very important!)
- Verify install: open Terminal (Mac) or Command Prompt (Windows) and run:
  ```
  python --version
  ```
  You should see something like `Python 3.11.5`

---

## Step 2: Open Terminal in the unzipped folder

- **Windows:** Open the folder in File Explorer → click the address bar → type `cmd` → press Enter
- **Mac:** Right-click the folder → "New Terminal at Folder"
- Or just `cd` into the folder:
  ```
  cd path/to/unzipped-folder
  ```

---

## Step 3: Install the required packages

Run this in the terminal:
```
pip install yfinance pandas
```
Wait for it to finish (30 seconds to 1 minute). You'll see lots of text — that's normal.

---

## Step 4: Run the BACKTEST first (do this today!)

```
python backtest.py
```

This will:
- Download 60 days of real NSE price data (free, from Yahoo Finance)
- Simulate every trade the bot would have made
- Print the win rate, total P&L, and estimated brokerage costs

**Look at the "Net P&L after costs" line.** If it's negative — that's crucial info. Don't proceed to live trading until backtest shows profit.

---

## Step 5: Run the PAPER TRADING bot (during market hours)

Market hours: **Monday to Friday, 9:15 AM to 3:30 PM IST**

```
python trading_bot.py
```

- Bot will wait for 9:30 AM, then start looking for signals
- Every "trade" is fake — no real money moves
- Watch the log lines to see what it's doing
- To stop the bot at any time: press **Ctrl + C**

Run this for **at least 2 weeks** before even thinking about going live.

---

## Step 6: (LATER — only after 2+ weeks of successful paper trading)

If (and ONLY if) the paper trading is showing consistent profit:

1. Log in to Groww on **web** (groww.in)
2. Go to [groww.in/trade-api](https://groww.in/trade-api) → subscribe to the Trading API
3. Groww Cloud → API Keys → click **"Generate TOTP token"**
4. Save your **TOTP Token** and **TOTP Secret** somewhere safe
5. Install extra packages:
   ```
   pip install growwapi pyotp
   ```
6. Open `trading_bot.py` in Notepad or any editor
7. Find the `CONFIG` section and update:
   ```python
   "TOTP_TOKEN": "paste_your_token_here",
   "TOTP_SECRET": "paste_your_secret_here",
   "PAPER_TRADING": False,       # <-- flip to False
   "TOTAL_CAPITAL": 5000,        # start with ₹5,000 MAX
   ```
8. In `BrokerInterface`, uncomment the Groww code lines (the ones starting with `#`)
9. Run: `python trading_bot.py`

---

## ⚠️ Golden Rules

1. **Never skip the backtest.** It's free and takes 5 minutes.
2. **Never skip paper trading.** Even if backtest is great, live behavior can differ.
3. **Start with ₹5,000 max.** Don't add more until profitable for 4+ weeks.
4. **Never share `trading_bot.py` with anyone once your TOTP keys are in it.**
5. **If you lose 3 days in a row → stop, review, don't just increase the amount.**

---

## 🆘 If Something Breaks

**"python: command not found"** → Python isn't in PATH. Reinstall and check the PATH box.

**"pip: command not found"** → Try `python -m pip install yfinance pandas` instead.

**"No trades executed. Check your data files"** → Almost always a yfinance data limit issue:
- yfinance's 1-min data is only available for the LAST 7 DAYS
- yfinance's 5-min data is available for the last 60 DAYS
- The backtest is already set to `INTERVAL = "5m"` and `LOOKBACK_DAYS = 60` — safest combo
- If still failing: open `backtest.py`, verify these two settings, and retry
- Also: weekends and market holidays have no data

**"No data returned for RELIANCE"** → Yahoo Finance rate-limited you. Wait 5 mins and retry.

**Bot shows no trades all day** → That's normal. ORB only trades when there's a clean breakout. Some days there are zero valid signals.

**Any other error** → Copy the full error message and paste it back to Claude. I'll debug it.

---

# 📖 The Rest of This Document (Reference Only)

## What This Bot Does

**Opening Range Breakout (ORB)** strategy on NSE stocks.

1. Watches 7 curated stocks at market open
2. Notes each stock's high/low during the first 15 minutes (9:15–9:30 AM)
3. If price breaks above opening high → buys
4. If it breaks below opening low → shorts
5. Uses auto stop-loss + 2:1 reward-to-risk target
6. Exits everything before market close (3:00 PM)

## Your Watchlist (already configured)

| # | Stock | Sector |
|---|-------|--------|
| 1 | RELIANCE | Energy/Conglomerate |
| 2 | TATAMOTORS | Auto |
| 3 | ICICIBANK | Banking |
| 4 | HDFCBANK | Banking |
| 5 | INFY | IT |
| 6 | TATASTEEL | Metals |
| 7 | ADANIENT | Diversified |

## Files In This Folder

| File | What it does |
|------|--------------|
| `trading_bot.py` | The live bot |
| `backtest.py` | Tests the strategy on past data |
| `README.md` | This file |

## Built-In Safety

- ✅ Max 3 trades per day
- ✅ Only 1% of capital risked per trade
- ✅ Max 2 stocks held at once
- ✅ Auto stop-loss on every trade
- ✅ Daily max-loss circuit breaker (₹300)
- ✅ Auto square-off at 3:00 PM (no overnight risk)

## Reality Check

- Most retail algo bots lose money — treat this as education first
- Brokerage + STT + slippage eats ~₹40 per round-trip trade
- ORB works in trending markets, struggles in choppy ones
- Track **NET** P&L (after all costs), not gross
- The bot is a tool, not a magic money machine

---

_Made with care. Start small. Stay safe. Good luck, Maddy! 🚀_
