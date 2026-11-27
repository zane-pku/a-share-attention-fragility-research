"""A-share reversal event study. Fixed case definitions, after-close signals."""
import argparse
from pathlib import Path
import json
import hashlib

import numpy as np
import pandas as pd

from backtest import load, load_review, outcomes, asof_rank

PERIODS = {"早期": ("2017-01-01","2019-12-31"), "中段": ("2020-01-01","2022-12-31"),
           "留出": ("2023-01-01","2026-11-23")}
MATCH_KEYS = ["ret5", "ret20", "vol"]
HORIZONS = [5,20,60]


def inputs(root, xlsx, etf_cache=None):
    f, close, manifest = load(root)
    x = json.loads((root/"public-snapshot.json").read_text(encoding="utf8"))["explorer"]
    prices = pd.DataFrame(dict(zip(x["index_names"],x["index_levels"],strict=True)),
                          index=pd.to_datetime(x["dates"])).loc[close.index]
    f["ret1"] = close.pct_change(fill_method=None)
    f["ret5"] = close.pct_change(5,fill_method=None)
    f["trend120"] = close.pct_change(120,fill_method=None)
    f["ret20"] = f["momentum20"]
    f["vol"] = f["volatility20"]
    if xlsx:
        _, ext, extra_manifest = load_review(xlsx,root,close,f)
        for k in ("limit_up_share5","limit_down_share5","advance_share5"):
            f[k] = ext[k].reindex(f.index)
        manifest["review_xlsx"] = extra_manifest
    if etf_cache:
        raw = etf_cache.read_bytes()
        shares = json.loads(raw)["shares"]
        index = pd.to_datetime(list(shares),format="%Y%m%d")
        held = pd.Series([rows.get("510300") for rows in shares.values()], index=index, dtype=float)
        if held.index.has_duplicates or held.dropna().le(0).any():
            raise ValueError("invalid ETF share observations")
        held = held.reindex(f.index)
        # Historical aggregate snapshot lacks first-seen records. Use a full-session lag.
        f["etf510300_growth5"] = held.pct_change(5,fill_method=None).shift(1)
        f["hs300_ret5"] = prices["沪深300"].pct_change(5,fill_method=None)
        valid_shares = held.dropna()
        manifest["etf_cache"] = dict(sha256=hashlib.sha256(raw).hexdigest(),
            source="wwww1998/national-team-etf-flow@c3b08d5376403e87a393b1a1fab8e628aded9ce9",
            code="510300",overlap_start=str(valid_shares.index[0].date()),
            overlap_end=str(valid_shares.index[-1].date()),overlap_days=len(valid_shares))
    return f, prices[["中证800","沪深300","中证1000"]], manifest


def signals(f):
    q = f.apply(asof_rank)
    def condition(columns, rule):
        eligible = q[columns].notna().all(axis=1) & q[MATCH_KEYS].notna().all(axis=1) & f.trend120.notna()
        return rule.where(eligible)
    cold = condition(["ret5","vol"],q.ret5.le(.10) & q.vol.ge(.8))
    margin = condition(["margin_growth20","ret5"],q.margin_growth20.le(.10) & f.ret5.lt(0))
    narrow = condition(["profit5","ret20"],q.profit5.le(.20) & f.ret20.gt(0))
    hot = condition(["profit20","ret20"],q.profit20.ge(.9) & f.ret20.gt(0))
    speculative = condition(["small_relative20","ret20"],q.small_relative20.ge(.9) & f.ret20.gt(0))
    rows = {"panic_price_vol":cold, "margin_contraction":margin, "breadth_divergence":narrow,
            "profit_heat":hot,"smallcap_heat":speculative}
    if "limit_down_share5" in f:
        pressure = condition(["limit_down_share5","ret5"],q.limit_down_share5.ge(.9) & f.ret5.lt(0))
        pressure_seen = pressure.astype(float).shift(1).rolling(3,min_periods=3).max()
        release = condition(["limit_down_share5","ret1"],
                            pressure_seen.eq(1) & f.ret1.gt(.01) & f.limit_down_share5.lt(f.limit_down_share5.shift(1)))
        release = release.where(pressure_seen.notna())
        chase = condition(["limit_up_share5","ret20"],q.limit_up_share5.ge(.9) & f.ret20.gt(0))
        rows.update(limit_down_panic=pressure,limit_down_release=release,limit_up_chase=chase)
    if "etf510300_growth5" in f:
        flow = q.etf510300_growth5.ge(.9) & f.etf510300_growth5.gt(0)
        rows.update(etf_dip_bid=condition(["etf510300_growth5","hs300_ret5"],flow & f.hs300_ret5.lt(0)),
                    etf_hot_flow=condition(["etf510300_growth5","hs300_ret5"],flow & f.hs300_ret5.gt(0)))
    return pd.DataFrame(rows), q[MATCH_KEYS].assign(bull=f.trend120.ge(0))


def select_onsets(status, position, horizon):
    start = status.eq(True) & status.shift(1).eq(False)
    # Use the first confirmed crossing. Missing-to-true is a left-censored episode.
    selected = []
    for date in status.index[start]:
        index = position.loc[date]
        if not selected or index-position.loc[selected[-1]] >= horizon:
            selected.append(date)
    return selected


def matches(anchors, model, positions, horizon, distance=.35):
    # Same calendar year and price regime. No use of future returns in matching.
    # Control dates can follow events and give a retrospective comparison.
    pool = model.loc[model.status.eq(False)]
    unused = set(pool.index)
    matched = {}
    for anchor in anchors:
        point = model.loc[anchor]
        candidates = pool.loc[(pool.index.year == anchor.year) & pool.bull.eq(point.bull)
                              & pool.index.isin(unused)]
        indices = positions.loc[candidates.index]
        candidates = candidates.loc[(indices-positions.loc[anchor]).abs().ge(horizon+1)]
        dist = (candidates[MATCH_KEYS]-point[MATCH_KEYS].astype(float)).abs()
        dist = dist.loc[dist.le(distance).all(axis=1)]
        if not dist.empty:
            other = dist.sum(axis=1).idxmin()
            unused.remove(other)
            matched[anchor] = other
    return matched


def path_stats(price,horizon,lag):
    value = outcomes(price,horizon,lag)
    return value.rename(columns={"return":"forward_return"}).drop(columns="event")


def run(f,prices, joint,lag=1):
    events, controls = signals(f)
    pos = pd.Series(range(len(f)),index=f.index)
    stats, ledger = [], []
    for benchmark, price in prices.items():
        for horizon in HORIZONS:
            y = path_stats(price,horizon,lag)
            for period,(start,end) in PERIODS.items():
                if joint:
                    end = min(end,"2026-07-30")
                valid = y.loc[start:end].loc[lambda d:d["end"].le(end)].dropna()
                for label in events:
                    frame = valid.join(events[label].rename("status")).join(controls).dropna()
                    if frame.empty: continue
                    onsets = select_onsets(events[label],pos,horizon)
                    dates = frame.index.intersection(onsets)
                    matched = matches(dates,frame,pos,horizon)
                    population = frame.loc[dates]
                    pairs = [(t,other) for t,other in matched.items()]
                    a = frame.loc[[t for t,_ in pairs]]
                    b = frame.loc[[other for _,other in pairs]]
                    delta = a.forward_return.to_numpy()-b.forward_return.to_numpy()
                    ddown = a.drawdown.to_numpy()-b.drawdown.to_numpy()
                    stats.append(dict(
                        universe="共同时段" if joint else "主样本",benchmark=benchmark,phase=period,
                        horizon=horizon,entry_lag=lag,signal=label,eligible_days=len(frame),
                        active_days=int(frame.status.eq(True).sum()),n_events=len(dates),n_matched=len(pairs),
                        all_days_return=frame.forward_return.mean(),event_return=population.forward_return.mean(),
                        event_median_return=population.forward_return.median(),event_drawdown=population.drawdown.mean(),
                        match_event_return=a.forward_return.mean(),match_control_return=b.forward_return.mean(),
                        match_spread=delta.mean() if len(delta) else np.nan,
                        match_median_spread=np.median(delta) if len(delta) else np.nan,
                        match_win_share=(delta>0).mean() if len(delta) else np.nan,
                        match_drawdown_spread=ddown.mean() if len(ddown) else np.nan))
                    for t,other in pairs:
                        ledger.append(dict(universe="共同时段" if joint else "主样本",benchmark=benchmark,phase=period,
                            horizon=horizon,entry_lag=lag,signal=label,date=t.date(),control_date=other.date(),
                            event_return=frame.at[t,"forward_return"],control_return=frame.at[other,"forward_return"],
                            event_drawdown=frame.at[t,"drawdown"],control_drawdown=frame.at[other,"drawdown"]))
    return pd.DataFrame(stats),pd.DataFrame(ledger)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--snapshot-dir",required=True,type=Path)
    p.add_argument("--review-xlsx",type=Path)
    p.add_argument("--etf-cache",type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    args.out.mkdir(exist_ok=True,parents=True)
    results=[]; ledger=[]
    for xlsx in [None,args.review_xlsx] if args.review_xlsx else [None]:
        f, prices, manifest = inputs(args.snapshot_dir,xlsx,args.etf_cache)
        if xlsx:
            cut = manifest["review_xlsx"]["last"]
            f, prices = f.loc[:cut], prices.loc[:cut]
        for lag in (1,2):
            a,b = run(f,prices,bool(xlsx),lag)
            results.append(a);ledger.append(b)
    result=pd.concat(results,ignore_index=True)
    result.to_csv(args.out/"event-study.csv",index=False,float_format="%.8f")
    pd.concat(ledger,ignore_index=True).to_csv(args.out/"matched-events.csv",index=False,float_format="%.8f")
    (args.out/"input-manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    cols=["universe","signal","n_events","n_matched","event_return","match_spread","match_drawdown_spread"]
    print(result.query('benchmark=="中证800" and phase=="留出" and horizon==20 and entry_lag==1')[cols].to_string(index=False))


if __name__=="__main__":
    main()

