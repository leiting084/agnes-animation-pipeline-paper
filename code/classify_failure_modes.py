#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
失败模式分类 + 场景混淆自动校验

输入 : data/audit_records_s01e01.json
输出 : results/failure_modes.csv 及一份场景分层报告

设计原则
--------
1. 【不做硬编码结论】本脚本只做分层、标记与统计，产出供人工标注的候选集。
   任何"面部崩坏占 X%"之类的结论，必须由人工判定后填入，脚本不代劳。

2. 【优先告警而非静默聚合】跨场景混淆是这批数据最大的陷阱
   (s76/s80/s90 为场景号而非批次号，通过率分别为 0/0/0，s100 为 83%)。
   脚本在聚合前强制先做场景分层校验，并在检测到混淆风险时中止输出。

用法
----
    python classify_failure_modes.py
    python classify_failure_modes.py --no-guard     # 跳过混淆校验，仅供调试
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

DEFAULT_DATA = (
    Path(__file__).resolve().parent.parent / "data" / "audit_records_s01e01.json"
)
DEFAULT_OUT = Path(__file__).resolve().parent.parent / "results" / "failure_modes.csv"

# 疑似运动抖动阈值。取值依据见 results/ 下的阈值扫描记录，非绝对判据。
SPIKE_SUSPECT = 1
MEAN_SUSPECT = 3.0


def load(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def flatten(records: dict) -> list[dict]:
    """把 {场景号: [记录]} 摊平成 [{scene, record}]"""
    return [{"scene": scene, **rec} for scene, recs in records.items() for rec in recs]


def scene_report(flat: list[dict]) -> dict:
    """按场景统计通过/判退分布"""
    report = {}
    for scene in sorted({row["scene"] for row in flat}):
        rows = [r for r in flat if r["scene"] == scene]
        acc = [r for r in rows if r.get("in_v9_final")]
        report[scene] = {
            "total": len(rows),
            "accepted": len(acc),
            "rejected": len(rows) - len(acc),
            "pass_rate": len(acc) / len(rows) if rows else 0.0,
            "mean_motion": (
                st.mean(r["motion"]["mean"] for r in rows if r.get("motion"))
                if any(r.get("motion") for r in rows)
                else 0.0
            ),
        }
    return report


def detect_confounding(report: dict) -> list[str]:
    """
    场景混淆检测。

    两个信号：
      A. 存在通过率为 0% 的场景 —— 说明该场景整批未过，
         此时跨场景对比 = 拿"没通过的场景"跟"通过的场景"比，因果不可解读。
      B. 通过率离散度过大 —— 场景间差异远超样本内差异。
    """
    warnings: list[str] = []

    zero_pass = [s for s, v in report.items() if v["pass_rate"] == 0.0]
    if zero_pass:
        warnings.append(
            f"[A] 存在通过率为 0% 的场景：{', '.join(zero_pass)}。"
            f"这些是场景号而非批次号，整批未通过意味着跨场景对比的因果不可解读。"
        )

    rates = [v["pass_rate"] for v in report.values()]
    if rates and (max(rates) - min(rates)) > 0.3:
        warnings.append(
            f"[B] 场景间通过率差异达 {(max(rates) - min(rates)) * 100:.0f} 个百分点，"
            f"远超场景内波动，跨场景聚合结果不可信。"
        )
    return warnings


def classify(flat: list[dict], report: dict) -> list[dict]:
    """逐条打标，产出人工复核用候选集"""
    out = []
    for row in flat:
        rec = {k: v for k, v in row.items() if k != "scene"}
        m = rec.get("motion") or {}
        accepted = bool(rec.get("in_v9_final"))

        flags = []
        if m.get("spikes_gt_20", 0) >= SPIKE_SUSPECT:
            flags.append("motion_suspect")
        if m.get("mean", 0) >= MEAN_SUSPECT:
            flags.append("high_mean_motion")
        if not flags:
            flags.append("no_motion_signal")

        out.append(
            {
                "file": rec.get("file", ""),
                "scene": row["scene"],
                "verdict": "accepted" if accepted else "rejected",
                "motion_mean": m.get("mean", ""),
                "motion_max": m.get("max", ""),
                "spikes_gt_20": m.get("spikes_gt_20", ""),
                "total_diffs": m.get("total_diffs", ""),
                "flags": "|".join(flags),
                "is_motion_candidate": "motion_suspect" in flags or "high_mean_motion" in flags,
                "has_audio": rec.get("has_audio", ""),
                "resolution": rec.get("resolution", ""),
            }
        )
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=DEFAULT_DATA)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--no-guard", action="store_true", help="跳过混淆校验")
    args = ap.parse_args()

    if not args.data.exists():
        print(f"数据文件不存在: {args.data}", file=sys.stderr)
        return 1

    records = load(args.data)
    flat = flatten(records)
    report = scene_report(flat)
    warnings = detect_confounding(report)

    print("=" * 68)
    print("场景分层报告")
    print("=" * 68)
    print(f"{'场景':<8}{'总数':<7}{'通过':<7}{'判退':<7}{'通过率':<10}{'motion均值'}")
    for scene, v in report.items():
        print(
            f"{scene:<8}{v['total']:<7}{v['accepted']:<7}{v['rejected']:<7}"
            f"{v['pass_rate'] * 100:>6.1f}%   {v['mean_motion']:.2f}"
        )

    total = len(flat)
    acc = sum(1 for r in flat if r.get("in_v9_final"))
    print(f"\n全局：共 {total} 条，通过 {acc}，判退 {total - acc}，"
          f"一次通过率 {acc / total * 100:.1f}%")

    print("\n" + "=" * 68)
    if warnings and not args.no_guard:
        print("⚠️  场景混淆告警 —— 以下分析禁止跨场景聚合")
        print("=" * 68)
        for w in warnings:
            print(f"  {w}")
        print("\n已中止输出，以避免生成误导性统计。")
        print("如需继续，请加 --no-guard（结果仅供调试）。")
        return 2

    if warnings:
        print("场景混淆告警（已按 --no-guard 忽略）")
        for w in warnings:
            print(f"  {w}")

    rows = classify(flat, report)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    cand = [r for r in rows if r["is_motion_candidate"]]
    print(f"\n已写出: {args.out}")
    print(f"运动异常候选 {len(cand)} / {len(rows)} 条 → 交人工判定具体失效模式")

    # 场景内对照提示（唯一干净的对照来源）
    print("\n可做的场景内对照：")
    for scene, v in report.items():
        if v["accepted"] and v["rejected"]:
            print(f"  ✅ {scene}: 同场景内既有通过也有判退，可做组内对照")

    print("\n注意：通过但携带高 spikes 的样本说明 spikes 非硬判据，")
    print("      不能仅凭运动指标判定质量。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
