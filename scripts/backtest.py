import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

FACTORS = {
    "turnover_concentration": ("baseline", "上游公开市场成交集中度原序列", 0),
    "momentum20": ("market", "20日中证800收益", 0),
    "volatility20": ("market", "20日中证800日收益标准差", 0),
    "profit5": ("market", "5日中证800成分跑赢指数比例均值", 0),
    "profit20": ("market", "20日中证800成分跑赢指数比例均值", 0),
    "weak_breadth": ("interaction", "20日动量分位减5日赚钱效应分位", 0),
    "abnormal_turnover": ("market", "当日成交额除过去60日中位数再取对数", 0),
    "small_relative20": ("market", "中证1000相对沪深300的20日相对收益", 0),
    "margin_growth20": ("market", "融资余额20日增长率", 1),
    "overheat": ("interaction", "动量、成交和融资增长三个历史分位的等权均值", 1),
}
FILES = ["public-snapshot.json", "market-profit-effect-snapshot.json", "financing-snapshot.json"]
SPLITS = {"开发": ("2012-01-01", "2019-12-31"), "验证": ("2020-01-01", "2022-12-31"),
          "留出": ("2023-01-01", "2026-11-23")}
CONTROLS = ["momentum20", "volatility20", "abnormal_turnover"]


def series(dates, values):
    result = pd.Series(values, index=pd.to_datetime(dates), dtype=float)
    if not result.index.is_monotonic_increasing or not result.index.is_unique:
        raise ValueError("Input dates must be unique and sorted")
    return result


def asof_rank(values, window=252, minimum=126):
    def position(arr):
        latest = arr[-1]
        past = arr[:-1]
        past = past[np.isfinite(past)]
        if not np.isfinite(latest) or len(past) < minimum:
            return np.nan
        return ((past < latest).sum() + 0.5 * (past == latest).sum()) / len(past)
    return values.rolling(window + 1, min_periods=minimum + 1).apply(position, raw=True)


def load(root):
    raw = [(root / name).read_bytes() for name in FILES]
    market, profit, finance = (json.loads(b) for b in raw)
    x = market["explorer"]
    prices = pd.DataFrame({name: series(x["dates"], levels)
                           for name, levels in zip(x["index_names"], x["index_levels"], strict=True)})
    prices = prices.loc[:"2026-11-23"]
    prices = prices.where(prices.gt(0))
    close = prices["中证800"]
    if close.isna().any():
        raise ValueError("Benchmark close is missing")
    t = next(q for q in profit["targets"] if q["key"] == "csi800")
    b = series(t["dates"], t["profit_effect"]).reindex(close.index)
    if ((b.dropna() < 0) | (b.dropna() > 1)).any():
        raise ValueError("Breadth must lie in [0, 1]")
    m = finance["market"]
    margin = series(m["dates"], m["margin_balance_100m"]).reindex(close.index)
    margin = margin.where(margin.gt(0)).shift(1)
    turnover = series(x["dates"], x["turnover_total_yi"]).reindex(close.index)
    turnover = turnover.where(turnover.gt(0))
    f = pd.DataFrame(index=close.index)
    f["turnover_concentration"] = series(x["dates"], x["crowding"]).reindex(close.index)
    f["momentum20"] = close.pct_change(20, fill_method=None)
    f["volatility20"] = close.pct_change(fill_method=None).rolling(20).std()
    f["profit5"] = b.rolling(5).mean()
    f["profit20"] = b.rolling(20).mean()
    f["weak_breadth"] = asof_rank(f["momentum20"]) - asof_rank(f["profit5"])
    f["abnormal_turnover"] = np.log(turnover / turnover.shift(1).rolling(60).median())
    f["small_relative20"] = (prices["中证1000"] / prices["沪深300"]).pct_change(20, fill_method=None)
    f["margin_growth20"] = margin.pct_change(20, fill_method=None)
    f["overheat"] = pd.concat([asof_rank(f[k]) for k in
                               ["momentum20", "abnormal_turnover", "margin_growth20"]], axis=1).mean(axis=1, skipna=False)
    manifest = {name: {"sha256": hashlib.sha256(data).hexdigest(),
                       "bytes": len(data), "generated_at": obj.get("generated_at"),
                       "origin": obj.get("data_source", obj.get("source", obj.get("sources")))}
                for name, data, obj in zip(FILES, raw, (market, profit, finance), strict=True)}
    return f, close, manifest


def outcomes(close, horizon, lag):
    path = pd.concat([close.shift(-k) for k in range(lag, lag+horizon+1)], axis=1)
    denominator = path.iloc[:, 0]
    path = path.div(denominator, axis=0)
    worst = (path / np.maximum.accumulate(path.to_numpy(), axis=1) - 1).min(axis=1, skipna=False)
    dates = pd.Series(close.index, index=close.index)
    threshold = -0.04 if horizon == 5 else -0.08
    return pd.DataFrame({"return": path.iloc[:, -1] - 1, "drawdown": worst,
                         "event": worst.le(threshold).where(worst.notna()), "end": dates.shift(-(lag+horizon))})


def paired_hac(frame, factor, target, horizon, controls):
    cols = [factor, *controls]
    d = frame[[*cols, target]].dropna()
    if len(d) < 100 or (d[cols].std() == 0).any():
        return (np.nan,) * 4
    x = (d[cols] - d[cols].mean()) / d[cols].std()
    fit = sm.OLS(d[target].astype(float), sm.add_constant(x)).fit(
        cov_type="HAC", cov_kwds={"maxlags": horizon, "use_correction": True})
    return fit.params[factor], fit.conf_int().loc[factor, 0], fit.conf_int().loc[factor, 1], fit.pvalues[factor]


def evaluate(f, close):
    ranks = f.apply(asof_rank)
    rows, regressions, robustness = [], [], []
    for lag in (1, 2):
        for horizon in (5, 20):
            y = outcomes(close, horizon, lag)
            for split, (start, end) in SPLITS.items():
                eligible = y.loc[start:end].loc[lambda d: d["end"].le(end)]
                for factor in FACTORS:
                    d = eligible.join(ranks[factor].rename("rank")).dropna()
                    if d.empty:
                        continue
                    hi, lo = d["rank"].ge(.8), d["rank"].le(.2)
                    stats = dict(split=split, lag=lag, horizon=horizon, factor=factor,
                                 start=d.index[0].date(), end=d.index[-1].date(), n=len(d),
                                 coverage=len(d)/len(eligible), n_high=int(hi.sum()), n_low=int(lo.sum()))
                    for col in ("return", "drawdown", "event"):
                        stats[f"all_{col}"] = d[col].mean()
                        stats[f"high_{col}"] = d.loc[hi, col].mean()
                        stats[f"low_{col}"] = d.loc[lo, col].mean()
                        stats[f"spread_{col}"] = stats[f"high_{col}"] - stats[f"low_{col}"]
                    stats["rank_ic_return"] = d["rank"].corr(d["return"], method="spearman")
                    stats["rank_ic_drawdown"] = d["rank"].corr(d["drawdown"], method="spearman")
                    rows.append(stats)
                    controls = [q for q in CONTROLS if q != factor] if factor in CONTROLS else [*CONTROLS, *([] if factor == "turnover_concentration" else ["turnover_concentration"])]
                    if lag == 1:
                        model = eligible.join(ranks[[factor, *controls]])
                        for target in ("return", "drawdown", "event"):
                            beta, lower, upper, p = paired_hac(model, factor, target, horizon, controls)
                            regressions.append(dict(split=split,horizon=horizon,factor=factor,target=target,
                                n=len(model.dropna()),beta=beta,lower95=lower,upper95=upper,p=p))
                    if horizon == 20:
                        # All phases of the fixed 20-trading-day grid. Each grid has disjoint return intervals.
                        positions = close.index.get_indexer(d.index)
                        for phase in range(20):
                            g = d.loc[positions % 20 == phase]
                            high = g[g["rank"].ge(.8)]
                            low = g[g["rank"].le(.2)]
                            if min(len(high), len(low)) >= 3:
                                robustness.append(dict(split=split,lag=lag,factor=factor,phase=phase,n=len(g),
                                    n_high=len(high),n_low=len(low),
                                    spread_return=high["return"].mean()-low["return"].mean(),
                                    spread_event=high["event"].mean()-low["event"].mean()))
    return pd.DataFrame(rows), pd.DataFrame(regressions), pd.DataFrame(robustness)


def out_of_sample(f, close):
    """Expanding, annual refits. Each augmented fit uses its baseline's identical rows."""
    base = [*CONTROLS, "turnover_concentration"]
    y = outcomes(close, 20, 1)
    ranks = f.apply(asof_rank)
    model = y.join(ranks)
    comparisons = []
    for factor in set(FACTORS).difference(base):
        d = model[[*base, factor, "event", "end"]].dropna()
        for year in range(2020, 2027):
            start = pd.Timestamp(year=year, month=1, day=1)
            end = pd.Timestamp(year=year+1, month=1, day=1)
            train = d.loc[(d.index >= "2012-01-01") & (d["end"] < start)]
            test = d.loc[(d.index >= start) & (d.index < end)]
            if len(train) < 250 or len(test) < 30 or train["event"].nunique() < 2:
                continue
            actual = test["event"].astype(float)
            b = {}
            for label, columns in [("base", base), ("augmented", [*base, factor])]:
                design = sm.add_constant(train[columns], has_constant="add")
                fit = sm.GLM(train["event"].astype(float), design, family=sm.families.Binomial()).fit()
                pred = fit.predict(sm.add_constant(test[columns], has_constant="add")).clip(1e-9, 1-1e-9)
                b[label] = (((pred-actual)**2).mean(), -(actual*np.log(pred)+(1-actual)*np.log1p(-pred)).mean())
            comparisons.append(dict(factor=factor,year=year,train_n=len(train),test_n=len(test),
                event_rate=actual.mean(),base_brier=b["base"][0],augmented_brier=b["augmented"][0],
                delta_brier=b["augmented"][0]-b["base"][0],base_logloss=b["base"][1],
                augmented_logloss=b["augmented"][1],delta_logloss=b["augmented"][1]-b["base"][1]))
    return pd.DataFrame(comparisons).sort_values(["factor","year"])


def load_review(book, root, close, f):
    xlsx = pd.ExcelFile(book, engine="openpyxl")
    cols = ["日期", "上证%", "创业板%", "上涨家数", "下跌家数", "涨停家数", "跌停家数", "封板率"]
    items = [pd.read_excel(xlsx, sheet_name=name, usecols=cols)
             for name in xlsx.sheet_names if name.isdigit()]
    data = pd.concat(items).dropna(subset="日期")
    date = pd.to_datetime(data.pop("日期"), format="%Y-%m-%d", errors="coerce")
    data = data.loc[date.notna()].set_index(date.dropna()).sort_index()
    if data.index.has_duplicates or not data.index.isin(close.index).all():
        raise ValueError("Review dates failed benchmark calendar check")
    x = json.loads((root / FILES[0]).read_text(encoding="utf8"))["explorer"]
    metrics = {}
    for column, name in (("上证%", "上证指数"), ("创业板%", "创业板指")):
        ref = series(x["dates"], x["index_levels"][x["index_names"].index(name)]).pct_change(fill_method=None)
        pct = pd.to_numeric(data[column].astype(str).str.rstrip("%"), errors="coerce") / 100
        absolute = (pct - ref.reindex(data.index)).abs()
        metrics[column] = {"n":int(absolute.count()), "miss_or_abs_diff_gt_6bp":int((absolute.isna() | absolute.gt(.0006)).sum()),
                           "median_absolute_error":float(absolute.median())}
        if metrics[column]["miss_or_abs_diff_gt_6bp"]:
            raise ValueError(f"Review return/date audit failed for {column}")
    up, down, lu, ld = (pd.to_numeric(data[k], errors="coerce").where(lambda q: q.ge(0))
                         for k in ["上涨家数","下跌家数","涨停家数","跌停家数"])
    total = (up + down).where(lambda q: q.gt(0))
    seal = pd.to_numeric(data["封板率"].astype(str).str.rstrip("%"), errors="coerce") / 100
    close = close.loc[:data.index[-1]]
    f = f.reindex(close.index).copy()
    supplemental = {
        "advance_share5": ("5日上涨/(上涨+下跌)均值", (up/total).reindex(close.index).rolling(5).mean()),
        "limit_up_share5": ("5日涨停/(上涨+下跌)均值", (lu/total).where(lu.le(up)).reindex(close.index).rolling(5).mean()),
        "limit_down_share5": ("5日跌停/(上涨+下跌)均值", (ld/total).where(ld.le(down)).reindex(close.index).rolling(5).mean()),
        "seal_failure5": ("5日未封板率均值，涨停家数为零的日期不推算", (1-seal.where(seal.between(0,1) & lu.gt(0))).reindex(close.index).rolling(5).mean()),
    }
    for key, (label, values) in supplemental.items():
        FACTORS[key] = ("external_review", label, 0)
        f[key] = values
    return close, f, {"sha256":hashlib.sha256(book.read_bytes()).hexdigest(),
                      "rows":len(data), "first":str(data.index[0].date()), "last":str(data.index[-1].date()),
                      "index_alignment":metrics,
                      "breadth_count_audit":{"limit_up_gt_advance":int(lu.gt(up).sum()),
                                             "limit_down_gt_decline":int(ld.gt(down).sum()),
                                             "zero_limit_up":int(lu.eq(0).sum())}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("results"))
    parser.add_argument("--review-xlsx", type=Path, help="Optional TDX-derived review workbook")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    f, close, manifest = load(args.snapshot_dir)
    if args.review_xlsx:
        close, f, review_info = load_review(args.review_xlsx, args.snapshot_dir, close, f)
        manifest["review_xlsx"] = review_info
    result, regressions, phases = evaluate(f, close)
    for name, data in [("tail_groups", result), ("conditional_hac", regressions), ("nonoverlap_phases", phases)]:
        data.to_csv(args.out / (name + ".csv"), index=False, float_format="%.8f")
    out_of_sample(f, close).to_csv(args.out/"annual_prediction.csv",index=False,float_format="%.8f")
    (args.out / "input_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
    print(result.query("split == '留出' and lag == 1 and horizon == 20")
          [["factor","n","n_high","n_low","all_event","high_event","low_event","spread_return"]].to_string(index=False))


if __name__ == "__main__":
    main()

