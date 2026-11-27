"""Export already-computed market research factors as an offline signal feed."""
import argparse
import json
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from backtest import asof_rank, load

SELECTED = {
    "profit5":"ratio", "profit20":"ratio", "weak_breadth":"score_minus1_to_1",
    "margin_growth20":"ratio", "volatility20":"ratio", "small_relative20":"ratio",
    "abnormal_turnover":"log_ratio", "overheat":"score_0_1",
}


def export(snapshot_dir, start=None):
    features, _, manifest = load(snapshot_dir)
    times = [datetime.fromisoformat(v["generated_at"]) for v in manifest.values()]
    if any(t.utcoffset() is None for t in times):
        raise ValueError("each snapshot must declare a time zone")
    # The final archive proves availability as a bundle only, not historical first visibility.
    available = max(times).isoformat()
    ranks = features[list(SELECTED)].apply(asof_rank)
    records = []
    for day, values in features.loc[start:, list(SELECTED)].iterrows():
        for metric, unit in SELECTED.items():
            for suffix, value, selected_unit in [
                ("", values[metric], unit),
                ("_percentile", ranks.at[day,metric] * 100, "percentile_0_100"),
            ]:
                present = value == value
                records.append({"family":"market_risk","scope":"cn_market","date":day.date().isoformat(),
                                "metric":metric+suffix,"value":float(value) if present else None,
                                "unit":selected_unit,"available_at":available,
                                "state":"observed" if present else "unobserved",
                                "method":"market_archive_252d_v1"})
    return {"version":1,"records":records}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--snapshot-dir",required=True,type=Path)
    p.add_argument("--start")
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    payload=export(a.snapshot_dir,a.start)
    a.out.write_text(json.dumps(payload,ensure_ascii=False,allow_nan=False,indent=2)+"\n",encoding="utf8")


if __name__=="__main__":
    main()

