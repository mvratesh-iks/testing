"""
================================================================
  TRADE ANALYZER
================================================================
  Reads trades.csv (produced by backtest.py) and gives you a
  detailed breakdown so you can see WHERE the money is going.

  Usage:
    1. First run: python backtest.py   (this creates trades.csv)
    2. Then run:  python analyze.py

  What you get:
    - Per-stock P&L  → which stocks to drop from watchlist
    - Time-of-day  → when to stop trading
    - Exit reason  → is stop-loss too tight? is EOD killing profits?
    - BUY vs SELL  → which side works better
    - Day-of-week  → any weekday pattern
    - Actionable recommendations at the end
================================================================
"""

import csv
import os
from collections import defaultdict
from datetime import datetime

BROKERAGE_PER_TRADE = 40   # rough estimate, ₹ per round-trip


def load_trades():
    if not os.path.exists("trades.csv"):
        print("❌ trades.csv not found. Run 'python backtest.py' first.")
        return []

    trades = []
    with open("trades.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["entry"]   = float(row["entry"])
            row["exit"]    = float(row["exit"])
            row["qty"]     = int(row["qty"])
            row["pnl"]     = float(row["pnl"])
            row["net_pnl"] = row["pnl"] - BROKERAGE_PER_TRADE   # after costs
            row["date_obj"] = datetime.strptime(row["date"], "%Y-%m-%d")
            trades.append(row)
    return trades


def print_header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def stats_line(label, trades, width=18):
    """Format a stat line: label | count | win% | gross | net"""
    if not trades:
        return f"  {label:<{width}} 0 trades"
    n = len(trades)
    wins = sum(1 for t in trades if t["pnl"] > 0)
    win_pct = wins / n * 100
    gross = sum(t["pnl"] for t in trades)
    net = sum(t["net_pnl"] for t in trades)
    marker = "✅" if net > 0 else "❌"
    return (f"  {marker} {label:<{width}} {n:>4} trades | "
            f"Win: {win_pct:>5.1f}% | Net: ₹{net:>+9,.0f}")


# ================================================================
# ANALYSIS FUNCTIONS
# ================================================================

def analyze_per_stock(trades):
    print_header("PER-STOCK BREAKDOWN (net of ₹40/trade brokerage)")
    by_stock = defaultdict(list)
    for t in trades:
        by_stock[t["symbol"]].append(t)

    # Sort by net P&L descending
    ranked = sorted(by_stock.items(),
                    key=lambda x: sum(t["net_pnl"] for t in x[1]),
                    reverse=True)
    for symbol, ts in ranked:
        print(stats_line(symbol, ts))

    # Identify losers to drop
    losers = [s for s, ts in ranked if sum(t["net_pnl"] for t in ts) < 0]
    if losers:
        print(f"\n  🔻 Losing stocks (consider dropping): {', '.join(losers)}")


def analyze_by_hour(trades):
    print_header("TIME-OF-DAY BREAKDOWN")
    # Bucket entries by hour of entry (we don't have exact entry time
    # in CSV, so we approximate by exit_reason patterns; but if you
    # add entry_time to the CSV later this improves).
    # For now, bucket by exit_reason as proxy for timing.

    # Since we don't have hour in CSV yet, let's group by exit reason
    # which IS a time signal (EOD = held all day, TARGET/SL = intraday)
    for reason in ["TARGET", "STOP-LOSS", "EOD"]:
        subset = [t for t in trades if t["exit_reason"] == reason]
        print(stats_line(reason, subset, width=15))

    eod = [t for t in trades if t["exit_reason"] == "EOD"]
    if eod and sum(t["net_pnl"] for t in eod) < 0:
        print(f"\n  🔻 EOD square-offs are losing money → trades aren't")
        print(f"     hitting targets. Consider tighter targets (1.5x risk instead of 2x)")


def analyze_by_side(trades):
    print_header("BUY vs SELL (which direction works)")
    buys  = [t for t in trades if t["side"] == "BUY"]
    sells = [t for t in trades if t["side"] == "SELL"]
    print(stats_line("BUY (breakout up)",   buys,  width=20))
    print(stats_line("SELL (breakdown)",    sells, width=20))

    if buys and sells:
        buy_net  = sum(t["net_pnl"] for t in buys)
        sell_net = sum(t["net_pnl"] for t in sells)
        if buy_net < 0 and sell_net > 0:
            print("\n  💡 BUY side loses, SELL wins → market is trending DOWN")
            print("     Consider disabling BUY signals in current conditions")
        elif sell_net < 0 and buy_net > 0:
            print("\n  💡 SELL side loses, BUY wins → market is trending UP")
            print("     Consider disabling SELL signals in current conditions")


def analyze_by_weekday(trades):
    print_header("DAY-OF-WEEK BREAKDOWN")
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    by_day = defaultdict(list)
    for t in trades:
        by_day[t["date_obj"].weekday()].append(t)

    for i, name in enumerate(weekdays):
        print(stats_line(name, by_day.get(i, []), width=15))


def analyze_streaks(trades):
    print_header("CONSECUTIVE LOSSES (worst losing streak)")
    sorted_trades = sorted(trades, key=lambda t: t["date_obj"])

    current_streak = 0
    max_streak = 0
    max_streak_loss = 0
    current_loss = 0

    for t in sorted_trades:
        if t["net_pnl"] < 0:
            current_streak += 1
            current_loss += t["net_pnl"]
            if current_streak > max_streak:
                max_streak = current_streak
                max_streak_loss = current_loss
        else:
            current_streak = 0
            current_loss = 0

    print(f"  Longest losing streak:   {max_streak} trades in a row")
    print(f"  Total damage from streak: ₹{max_streak_loss:,.2f}")

    if max_streak >= 5:
        print(f"\n  ⚠️  A {max_streak}-trade losing streak is brutal psychologically.")
        print(f"     Add a rule: stop trading after 3 losses in a row for the day.")


def analyze_win_loss_size(trades):
    print_header("RISK/REWARD REALITY CHECK")
    wins   = [t["pnl"] for t in trades if t["pnl"] > 0]
    losses = [t["pnl"] for t in trades if t["pnl"] < 0]

    if not wins or not losses:
        return
    avg_win = sum(wins) / len(wins)
    avg_loss = abs(sum(losses) / len(losses))
    rr_ratio = avg_win / avg_loss

    print(f"  Average winning trade:  ₹{avg_win:>7,.2f}")
    print(f"  Average losing trade:   ₹{-avg_loss:>7,.2f}")
    print(f"  Actual R:R ratio:       {rr_ratio:.2f} : 1")
    print(f"  (Strategy targeted 2:1 — is real ratio close to that?)")

    win_pct = len(wins) / len(trades) * 100
    breakeven_win_pct = 100 / (1 + rr_ratio)
    print(f"\n  Your win rate:          {win_pct:.1f}%")
    print(f"  Breakeven win rate:     {breakeven_win_pct:.1f}%  (need above this)")

    if win_pct < breakeven_win_pct:
        gap = breakeven_win_pct - win_pct
        print(f"\n  🔻 You're {gap:.1f}% below breakeven — strategy needs win rate to")
        print(f"     go up, OR average win size to go up, OR fewer trades.")


def recommendations(trades):
    print_header("💡 ACTIONABLE RECOMMENDATIONS")

    total_net = sum(t["net_pnl"] for t in trades)
    n = len(trades)

    # Recommendation 1: too many trades?
    trades_per_day = n / 60  # 60 days lookback
    if trades_per_day > 3:
        print(f"  1. Too many trades ({trades_per_day:.1f}/day).")
        print(f"     Brokerage is eating you alive.")
        print(f"     → Add filters: minimum breakout %, volume confirmation.")

    # Recommendation 2: losing stocks
    by_stock = defaultdict(list)
    for t in trades:
        by_stock[t["symbol"]].append(t)
    losers = [s for s, ts in by_stock.items() if sum(t["net_pnl"] for t in ts) < 0]
    if losers:
        print(f"\n  2. Drop these stocks from watchlist: {', '.join(losers)}")
        print(f"     They lost money over the last 60 days.")

    # Recommendation 3: exit reason
    eod = [t for t in trades if t["exit_reason"] == "EOD"]
    eod_pct = len(eod) / n * 100 if n else 0
    if eod_pct > 30:
        print(f"\n  3. {eod_pct:.0f}% of trades exit at EOD (not hitting target).")
        print(f"     → Reduce target from 2x risk to 1.5x — take profits earlier.")

    # Recommendation 4: overall verdict
    print(f"\n  4. Overall verdict:")
    if total_net > 0:
        print(f"     ✅ Strategy is net positive. Move to live paper trading.")
    elif total_net > -2000:
        print(f"     ⚠️  Slightly negative. Fixable with 2-3 filter tweaks.")
    else:
        print(f"     ❌ Significantly negative ({total_net:,.0f}). Needs bigger changes:")
        print(f"        - Different strategy (RSI, MA crossover)")
        print(f"        - OR much tighter filters on this ORB")


# ================================================================
# RUN
# ================================================================

def main():
    trades = load_trades()
    if not trades:
        return

    print(f"\n📊 Analyzing {len(trades)} trades...\n")

    analyze_per_stock(trades)
    analyze_by_side(trades)
    analyze_by_hour(trades)
    analyze_by_weekday(trades)
    analyze_streaks(trades)
    analyze_win_loss_size(trades)
    recommendations(trades)

    print("\n" + "=" * 60)
    print("  Analysis complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
