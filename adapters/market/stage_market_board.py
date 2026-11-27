"""Validate standalone provider exports and create an offline market board preview."""
import argparse
from datetime import date, datetime, timedelta, timezone
import json
from math import isfinite
from pathlib import Path
import re

LOCAL = timezone(timedelta(hours=8))
CATEGORIES = {"crowding":"cn_crowding","market_risk":"market_risk",
              "community":"community_attention","shortline":"shortline"}
UNITS = {"ratio","multiple","score_0_100","percentile_0_100","score_minus1_to_1",
         "score_0_1","log_ratio","count"}
BOUNDS = {"score_0_100":(0,100),"percentile_0_100":(0,100),
          "score_0_1":(0,1),"score_minus1_to_1":(-1,1)}
CROWDING_NAMES = {"s":"成交额份额","q":"规模修正成交倍数","d":"个股成交偏离",
                  "u_plus":"上涨侧成交份额"}
BASE_FIELDS = {"family","scope","date","metric","value","unit","available_at","state","method"}
ID = re.compile(r"[a-z0-9_]{1,64}")


def aware(value):
    instant = datetime.fromisoformat(value)
    if instant.utcoffset() is None:
        raise ValueError("expected timezone-aware timestamp")
    return instant


def stage(payloads, as_of):
    now = aware(as_of)
    seen = set()
    series = {}
    for payload in payloads:
        if set(payload) != {"version","records"} or type(payload["version"]) is not int or payload["version"] != 1:
            raise ValueError("unsupported producer envelope")
        for row in payload["records"]:
            if not BASE_FIELDS <= row.keys() or set(row)-BASE_FIELDS-{"coverage"}:
                raise ValueError("missing or unsupported producer fields")
            fam, scope, metric, method = [row[key] for key in ("family","scope","metric","method")]
            if fam not in CATEGORIES or any(not ID.fullmatch(k) for k in (scope,metric,method)):
                raise ValueError("invalid producer identifiers")
            key = (fam, scope, metric)
            day = date.fromisoformat(row["date"])
            if day.isoformat() != row["date"]:
                raise ValueError("date must use YYYY-MM-DD")
            identity = (*key,day)
            if identity in seen:
                raise ValueError(f"duplicate observation: {identity}")
            seen.add(identity)
            value = row["value"]
            unit = row["unit"]
            state = row["state"]
            if state not in {"observed","unobserved"} or unit not in UNITS:
                raise ValueError("invalid observation state or unit")
            if (state=="observed") != (value is not None):
                raise ValueError("observed values and missing states disagree")
            if value is not None:
                if type(value) not in (float,int) or not isfinite(value):
                    raise ValueError("value must be a finite number")
                if unit in BOUNDS and not BOUNDS[unit][0] <= value <= BOUNDS[unit][1]:
                    raise ValueError("score exceeds unit scale")
                if unit == "count" and (value < 0 or int(value) != value):
                    raise ValueError("count must be a natural number")
            available = aware(row["available_at"]) if row["available_at"] is not None else None
            if (available is None and state=="observed") or (available and available.astimezone(LOCAL).date() < day):
                raise ValueError("last availability cannot precede the observation date")
            coverage = row.get("coverage")
            if coverage is not None and (type(coverage) not in (float,int) or not 0 <= coverage <= 1):
                raise ValueError("coverage must be between 0 and 1")
            if day > now.astimezone(LOCAL).date() or (available and available > now):
                continue
            section = series.setdefault(key, {"unit":unit,"method":method,"points":[]})
            if section["unit"] != unit or section["method"] != method:
                raise ValueError("split the feed at a methodology or unit change")
            section["points"].append(row)
    groups = {}
    possible = []
    for (fam, scope, metric), section in sorted(series.items()):
        points = sorted(section["points"],key=lambda r:r["date"])
        value_count = sum(x["state"]=="observed" for x in points)
        latest_seen = next((p for p in reversed(points) if p["state"] == "observed"), None)
        age = (now.astimezone(LOCAL).date() - date.fromisoformat(latest_seen["date"])).days if latest_seen else None
        groups.setdefault(CATEGORIES[fam],[]).append(
            {"scope":scope,"metric":metric,"unit":section["unit"],"method":section["method"],
             "n":len(points),"observed":value_count,"observation_rate":value_count/len(points),
             "latest":points[-1],"latest_observed":latest_seen,"calendar_age_days":age})
        factor = CROWDING_NAMES.get(metric.removesuffix("_5d_percentile"))
        if fam != "crowding" or not factor or not metric.endswith("_5d_percentile") or section["unit"] != "percentile_0_100" or not value_count:
            continue
        if len(possible)>=500 or value_count>5000:
            raise ValueError("crowding candidate exceeds platform batch limits")
        obs = []
        for point in points:
            if point["state"] != "observed":
                continue
            obs.append({"observedOn":point["date"],"value":point["value"],
                        "fetchedAt":aware(point["available_at"]).astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00","Z"),
                        "confidence":None,"dataSource":"sector_research_panel","dataSourceLabel":"行业研究行情衍生",
                        "sourceNote":"方法 "+point["method"],"citation":None,"sourceUrl":None,
                        "sourceTier":"derived","sourceTierLabel":"研究衍生","metricType":"sector_crowding_percentile",
                        "metricTypeLabel":factor+"历史分位","disclosedOn":None})
        possible.append({"seriesId":f"research_crowd_{scope}_{metric}","source":"research_sector_crowding_v1",
                         "name":f"{scope} {factor}历史分位","category":"cn_crowding","unit":"分位",
                         "enabled":False,"notes":"研究候选。使用独立序列 ID，启用需平台集成审查。",
                         "observations":obs})
    generated = now.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00","Z")
    return {"as_of":as_of,"sections":groups}, {
        "version":2,"requestedSource":"cn_crowding","generatedAt":generated,"series":possible}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--as-of",required=True)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("inputs",nargs="+",type=Path)
    a=p.parse_args()
    a.out.mkdir(exist_ok=True,parents=True)
    payloads=[json.loads(path.read_text(encoding="utf-8-sig")) for path in a.inputs]
    preview,batch=stage(payloads,a.as_of)
    for file,data in [("market-board-preview.json",preview),("crowding-refresh-candidate.json",batch)]:
        (a.out/file).write_text(json.dumps(data,ensure_ascii=False,allow_nan=False,indent=2)+"\n",encoding="utf8")


if __name__=="__main__":
    main()

