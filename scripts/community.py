"""Aggregate authorised platform-level counts. The input fixture is synthetic."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

METRICS = {"attention_share": ("mentions", "total_posts"),
           "question_rate": ("questions", "mentions"),
           "fomo_rate": ("chase", "mentions"),
           "panic_rate": ("panic", "mentions"),
           "net_tone": ("bull", "mentions")}
COUNTS = ["mentions", "total_posts", "questions", "chase", "panic", "bull", "bear"]
VALID = {"observed", "verified_zero", "unobserved"}


def checked_input(path):
    df = pd.read_csv(path)
    required = {"date", "topic", "platform", "status", "published_at", "mode", *COUNTS}
    if required.difference(df.columns):
        raise ValueError(f"Missing columns: {sorted(required.difference(df.columns))}")
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="raise")
    if df[["topic", "platform"]].isna().any().any():
        raise ValueError("Topic and platform are required")
    if df.duplicated(["date", "topic", "platform"]).any():
        raise ValueError("Duplicate date/topic/platform")
    allowed = df["status"].isin(VALID) & df["mode"].isin(["chronological", "ranked_feed"])
    if not allowed.all():
        raise ValueError("Invalid status or mode")
    if ((df["mode"] == "ranked_feed") & (df["status"] == "verified_zero")).any():
        raise ValueError("A ranked feed cannot establish verified zero")
    known = df["status"].ne("unobserved")
    counts = df[COUNTS].apply(pd.to_numeric, errors="raise")
    if counts.loc[known].isna().any().any():
        raise ValueError("Observed rows need all counts")
    if counts.loc[~known].notna().any().any():
        raise ValueError("Unobserved rows must leave counts blank")
    if ((counts < 0) | (counts.mod(1) != 0) & counts.notna()).any().any():
        raise ValueError("Counts must be nonnegative integers")
    if not (counts.loc[known, "total_posts"] >= counts.loc[known, "mentions"]).all():
        raise ValueError("Mentions exceed posts")
    for c in ["questions", "chase", "panic"]:
        if not counts.loc[known, c].le(counts.loc[known, "mentions"]).all():
            raise ValueError(f"{c} exceeds mentions")
    if not counts.loc[known, ["bull", "bear"]].sum(axis=1).le(counts.loc[known, "mentions"]).all():
        raise ValueError("Bull and bear are mutually exclusive")
    if not counts.loc[df["status"].eq("verified_zero"), "mentions"].eq(0).all():
        raise ValueError("Verified zero requires zero mentions")
    if not counts.loc[df["status"].eq("observed"), "mentions"].gt(0).all():
        raise ValueError("Observed requires positive mentions")
    timestamp = df.loc[known, "published_at"].astype(str)
    if not timestamp.str.contains(r"(?:Z|[+-]\d\d:\d\d)$", regex=True).all():
        raise ValueError("Publication time needs an explicit timezone")
    published = pd.to_datetime(timestamp, format="ISO8601", utc=True, errors="raise")
    day = df.loc[known, "date"].dt.tz_localize("Asia/Shanghai")
    cutoff = day + pd.Timedelta(hours=20)
    if not published.between(day, cutoff).all():
        raise ValueError("Aggregates were unavailable by the specified observation cutoff")
    df[COUNTS] = counts
    return df


def historical_position(values, lookback=60, minimum=30):
    def rank(a):
        past = a[:-1][np.isfinite(a[:-1])]
        if len(past) < minimum or not np.isfinite(a[-1]):
            return np.nan
        return ((past < a[-1]).sum() + 0.5*(past == a[-1]).sum())/len(past)
    return values.rolling(lookback+1, min_periods=minimum+1).apply(rank, raw=True)


def aggregate(df, calendar, config):
    platforms = config["platforms"]
    if len(platforms) < 2 or any(mode not in {"chronological", "ranked_feed"} for mode in platforms.values()):
        raise ValueError("Use at least two fixed platforms with declared modes")
    if not df["platform"].map(platforms).eq(df["mode"]).all():
        raise ValueError("Platform or mode differs from frozen configuration")
    if not pd.Index(df["date"]).isin(calendar).all():
        raise ValueError("Input date is absent from trading calendar")
    standard = df.set_index(["topic","platform","date"]).sort_index()
    results, audit = [], []
    for topic in sorted(df["topic"].unique()):
        frame = standard.loc[topic].reindex(
            pd.MultiIndex.from_product([platforms, calendar], names=["platform", "date"]))
        frame["status"] = frame["status"].fillna("unobserved")
        for metric, (numer, denom) in METRICS.items():
            rows = []
            for platform, mode in platforms.items():
                if metric == "attention_share" and mode != "chronological":
                    continue
                d = frame.loc[platform]
                n = d[denom]
                x = d[numer]
                if metric == "net_tone":
                    x = x - d["bear"]
                raw = x.div(n.where(n.gt(0)))
                rank = historical_position(raw)
                precision = n / (n + 20)
                # The decision series excludes weak coverage. Neutral participation is for display only.
                value = (.5 + (rank - .5)*precision).rename("value")
                rows.append(pd.DataFrame({"topic":topic, "platform":platform, "metric":metric,
                    "date":calendar, "raw":raw.to_numpy(), "rank":rank.to_numpy(),
                    "value":value.to_numpy(), "status":d["status"].to_numpy()}))
            if not rows:
                continue
            audit.extend(rows)
            observations = pd.concat(rows)
            panel = observations.pivot(index="date", columns="platform", values="value")
            count = panel.notna().sum(axis=1)
            covered = count / panel.shape[1]
            display = panel.fillna(.5).mean(axis=1)
            leave = pd.concat([panel.drop(columns=p).fillna(.5).mean(axis=1) for p in panel], axis=1)
            research = display.where(count.ge(2) & covered.ge(.5))
            results.append(pd.DataFrame({"topic":topic,"metric":metric,"date":calendar,
                "eligible_platforms":panel.shape[1],"valid_platforms":count.to_numpy(),
                "coverage":covered.to_numpy(),"display":display.where(count.gt(0)).to_numpy(),
                "research":research.to_numpy(),
                "leave_one_min":leave.min(axis=1).where(count.ge(2)).to_numpy(),
                "leave_one_max":leave.max(axis=1).where(count.ge(2)).to_numpy()}))
            if metric == "attention_share":
                rank_panel = observations.pivot(index="date", columns="platform", values="rank")
                active = rank_panel.ge(.8).astype(float).where(rank_panel.notna())
                # Partial coverage gives an interval. The research reading requires every eligible platform.
                lower = active.fillna(False).mean(axis=1)
                upper = active.fillna(True).mean(axis=1)
                leave_diffusion = pd.concat([active.drop(columns=p).mean(axis=1)
                                             for p in active], axis=1)
                full = count.eq(panel.shape[1]) & count.ge(2)
                results.append(pd.DataFrame({"topic":topic,"metric":"attention_diffusion","date":calendar,
                    "eligible_platforms":panel.shape[1],"valid_platforms":count.to_numpy(),
                    "coverage":covered.to_numpy(),"display":lower.where(count.gt(0)).to_numpy(),
                    "research":lower.where(full).to_numpy(),
                    "leave_one_min":leave_diffusion.min(axis=1).where(full).to_numpy(),
                    "leave_one_max":leave_diffusion.max(axis=1).where(full).to_numpy(),
                    "coverage_lower":lower.where(count.gt(0)).to_numpy(),
                    "coverage_upper":upper.where(count.gt(0)).to_numpy()}))
    if not results:
        raise ValueError("No valid topics or metrics")
    return pd.concat(results, ignore_index=True), pd.concat(audit, ignore_index=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--calendar", type=Path, required=True, help="CSV with date column")
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    calendar = pd.DatetimeIndex(pd.to_datetime(pd.read_csv(args.calendar)["date"], format="%Y-%m-%d"))
    if not len(calendar) or calendar.hasnans or not calendar.is_unique or not calendar.is_monotonic_increasing:
        raise ValueError("Calendar must have unique chronological dates")
    config = json.loads(args.config.read_text(encoding="utf-8-sig"))
    score, audit = aggregate(checked_input(args.input), calendar, config)
    args.out.mkdir(exist_ok=True, parents=True)
    score.to_csv(args.out/"community_signals.csv", index=False)
    audit.to_csv(args.out/"community_coverage.csv", index=False)


if __name__ == "__main__":
    main()


