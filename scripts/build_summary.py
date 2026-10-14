#!/usr/bin/env python3
"""Build report tables/figures from the untouched experiment exports.

Run from any directory: python scripts/build_summary.py
Requires numpy and matplotlib. Compilation uses only generated PDF/TeX files.
"""
import csv
import hashlib
import json
import math
import os
from collections import defaultdict
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/mlsys-report-matplotlib")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "summary"
THOR = Path("THOR/20261014_quality_complete")
AGX = Path("AGX/20261014_011851_agx_quantization_scan_summary/数据")
ADA = Path("ADA6000/20261013_complete_inference")
ADA_PREFIX = "20261013_213700_ada_"
INPUTS = {}


def read_csv(relative):
    path = ROOT / relative
    INPUTS[str(relative)] = {
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    INPUTS[str(relative)]["rows"] = len(rows)
    return rows


def f(row, key):
    return float(row[key])


def check_close(actual, expected, label):
    if not math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-7):
        raise ValueError(f"{label}: recomputed {actual}, exported {expected}")


def group(rows, key):
    result = defaultdict(list)
    for row in rows:
        result[row[key]].append(row)
    return result


def table(name, columns, header, rows):
    text = [r"\begin{tabular}{" + columns + "}", r"\toprule"]
    text += [" & ".join(header) + r" \\", r"\midrule"]
    text += [" & ".join(row) + r" \\" for row in rows]
    text += [r"\bottomrule", r"\end{tabular}", ""]
    (OUT / name).write_text("\n".join(text), encoding="utf-8")


def label(mode):
    if mode == "bf16":
        return "BF16"
    if mode == "original_bf16":
        return "原始 BF16"
    return f"T{int(mode[4:])}"


def style(axis, title, ylabel, xlabel="4-bit candidate layers (%)"):
    axis.set_title(title, loc="left", fontsize=11, fontweight="bold", pad=9)
    axis.set_xlabel(xlabel)
    axis.set_ylabel(ylabel)
    axis.grid(axis="y", color="#e4e9ef", linewidth=0.7)
    for side in ("top", "right"):
        axis.spines[side].set_visible(False)
    axis.set_axisbelow(True)


def save(fig, filename):
    fig.savefig(OUT / filename, bbox_inches="tight", metadata={"CreationDate": None})
    plt.close(fig)


def build():
    OUT.mkdir(exist_ok=True)
    thor = read_csv(THOR / "thor_observed3200_summary.csv")
    quality = read_csv(THOR / "thor_quality_modes_12.csv")
    clean = read_csv(THOR / "thor_clean_samples_360.csv")
    profiles = read_csv(THOR / "thor_profiles_180.csv")
    episodes = read_csv(THOR / "thor_quality_episodes_360.csv")
    tasks = read_csv(THOR / "thor_quality_tasks_120.csv")
    agx = read_csv(AGX / "渐进量化结果.csv")
    agx_config = read_csv(AGX / "实验配置与对照.csv")
    agx_raw = read_csv(AGX / "稳定延迟样本.csv")
    ada = read_csv(ADA / (ADA_PREFIX + "tiers.csv"))
    ada_raw = read_csv(ADA / (ADA_PREFIX + "raw_samples.csv"))

    # Check all plotted wall statistics against the original timed calls.
    ada_groups = group(ada_raw, "mode")
    for row in ada:
        values = [f(s, "wall_ms") for s in ada_groups[row["mode"]]]
        assert len(values) == int(row["repeat_count"]) == 10
        for q, key in [(50, "median_ms"), (10, "p10_ms"), (90, "p90_ms")]:
            check_close(np.percentile(values, q), f(row, key), "Ada " + row["mode"] + key)
    assert len(ada_raw) == 130
    assert all(r["vlm_calls"] == "1" and r["dit_calls"] == "1" for r in ada_raw)

    agx_groups = group(agx_raw, "experiment")
    for row in agx_config:
        values = [f(s, "wall_ms") for s in agx_groups[row["experiment"]]]
        assert len(values) == int(row["stable_samples"])
        check_close(np.median(values), f(row, "wall_median_ms"), "AGX " + row["experiment"])
    for row in agx:
        values = [f(s, "wall_ms") for s in agx_groups[f"tier{int(row['tier']):02d}"]]
        for q, key in [(25, "p25_ms"), (75, "p75_ms")]:
            check_close(np.percentile(values, q), f(row, key), "AGX " + row["tier"] + key)
    assert len(agx_raw) == 288
    assert all(r["profiler"].lower() == "false" for r in agx_raw)

    included = [r for r in clean if r["included_observed3200"].lower() == "true"]
    included_profiles = [r for r in profiles if r["included_observed3200"].lower() == "true"]
    assert len(clean) == 360 and len(included) == 247
    assert len(profiles) == 180 and len(included_profiles) == 122
    clean_groups = group(included, "mode")
    profile_groups = group(included_profiles, "mode")
    for row in thor:
        for samples, value_key, prefix in [
            (clean_groups[row["mode"]], "elapsed_ms", "clean_wall_ms"),
            (profile_groups[row["mode"]], "raw_kernel_ms", "raw_kernel_ms"),
        ]:
            visits = group(samples, "visit_id")
            medians = [np.median([f(s, value_key) for s in visit]) for visit in visits.values()]
            assert len(samples) == int(row[prefix + "_samples"])
            assert len(visits) == int(row[prefix + "_visits"])
            for stat, func in [("median", np.median), ("min", min), ("max", max)]:
                check_close(func(medians), f(row, prefix + "_" + stat), "Thor " + row["mode"] + stat)

    # Recompute all success counts and matched-pair outcomes from 360 episodes.
    episode_groups = group(episodes, "mode")
    baseline = {(r["task_id"], r["initial_state_index"]): r for r in episode_groups["bf16"]}
    fingerprint_keys = ["seed", "initial_state_sha256", "fixture_model_sha256", "settled_sim_state_sha256",
                        "initial_main_rgb_sha256", "initial_wrist_rgb_sha256", "visual_delay_ticks", "action_delay_ticks"]
    assert len(episodes) == 360 and len(baseline) == 30
    for row in quality:
        values = episode_groups[row["mode"]]
        assert len(values) == len({(r["task_id"], r["initial_state_index"]) for r in values}) == 30
        successes = losses = gains = 0
        for ep in values:
            ref = baseline[(ep["task_id"], ep["initial_state_index"])]
            assert all(ep[key] == ref[key] for key in fingerprint_keys)
            success, ref_success = ep["success"].lower() == "true", ref["success"].lower() == "true"
            successes += success
            losses += ref_success and not success
            gains += success and not ref_success
        assert successes == int(row["successes"])
        assert losses == int(row["baseline_only_success"]) and gains == int(row["tier_only_success"])
        check_close(successes / 30, f(row, "success_rate"), "Thor success " + row["mode"])
    for row in tasks:
        values = [r for r in episode_groups[row["mode"]] if r["task_id"] == row["task_id"]]
        assert len(values) == 3
        assert sum(r["success"].lower() == "true" for r in values) == int(row["successes"])

    blue, teal, orange = "#2463a5", "#168779", "#bb5d20"
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10.5, "axes.labelsize": 10.5,
                         "legend.fontsize": 9.5, "pdf.fonttype": 42, "lines.linewidth": 1.6})
    qmap = {r["mode"]: r for r in quality}
    tbase = f(thor[0], "clean_wall_ms_median")
    quant = thor[1:]
    tx = np.array([f(r, "fp4_candidate_pct") for r in quant])
    ty = np.array([f(r, "clean_wall_ms_median") for r in quant])
    low = np.array([f(r, "clean_wall_ms_min") for r in quant])
    high = np.array([f(r, "clean_wall_ms_max") for r in quant])
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 2.8), constrained_layout=True)
    axes[0].errorbar(tx, ty, yerr=[ty - low, high - ty], fmt="o-", color=blue, capsize=2, markersize=4,
                     label="Median of visit medians; min-max")
    axes[0].axhline(tbase, color="#65758a", linestyle="--", label=f"Fused BF16: {tbase:.2f} ms")
    style(axes[0], "A  Complete-call latency", "Wall latency (ms)")
    axes[0].set_ylim(61, 75)
    axes[0].legend(loc="upper right")
    axes[1].plot(tx, [100 * f(qmap[r["mode"]], "success_rate") for r in quant], "o-", color=teal, markersize=4,
                 label="Same 30 task/state pairs per mode")
    axes[1].axhline(100 * f(quality[0], "success_rate"), color="#65758a", linestyle="--", label="BF16: 19/30")
    style(axes[1], "B  Fixed-delay closed-loop pilot", "Success rate (%)")
    axes[1].set_ylim(0, 100)
    axes[1].legend(loc="lower right")
    save(fig, "thor_latency_quality.pdf")

    rows = []
    for r in thor:
        q = qmap[r["mode"]]
        rows.append([label(r["mode"]), "--" if r["mode"] == "bf16" else r["fp4_count"],
                     f"{f(r,'clean_wall_ms_median'):.2f}",
                     f"{f(r,'clean_wall_ms_min'):.2f}--{f(r,'clean_wall_ms_max'):.2f}",
                     r["clean_wall_ms_samples"] + "/" + r["clean_wall_ms_visits"],
                     f"{tbase/f(r,'clean_wall_ms_median'):.3f}", q["successes"] + "/30",
                     f"{f(q,'success_delta_vs_bf16_pp'):+.1f}",
                     q["baseline_only_success"] + "/" + q["tier_only_success"]])
    table("thor_table.tex", "lrrrrrrrr", ["配置", "FP4 层", "延迟/ms", "访问范围/ms", "$n/v$", "$S_q$",
                                           "成功", "$\\Delta$pp", "失去/新增"], rows)

    originals = {r["experiment"]: r for r in agx_config}
    goriginal = f(originals["bf16_original"], "wall_median_ms")
    gmatched = f(originals["bf16_matched"], "wall_median_ms")
    gx = [f(r, "w4_percent") for r in agx]
    gy = [f(r, "wall_median_ms") for r in agx]
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 2.8), constrained_layout=True)
    axes[0].plot(gx, gy, "o-", color=blue, markersize=4, label="Median; 12 calls/tier")
    axes[0].fill_between(gx, [f(r, "p25_ms") for r in agx], [f(r, "p75_ms") for r in agx], color=blue, alpha=.13,
                          label="P25-P75 of measured calls")
    axes[0].axhline(gmatched, color="#65758a", linestyle="--", label=f"Matched BF16: {gmatched:.2f} ms")
    style(axes[0], "A  Serial Flow request latency", "Wall latency (ms)")
    axes[0].set_ylim(370, 670)
    axes[0].legend(loc="upper right")
    for task, color in [(0, teal), (3, orange), (7, "#9765ac")]:
        axes[1].plot(gx, [f(r, f"raw_action_relative_l2_task{task}") for r in agx], "o-", color=color,
                     markersize=3.5, label=f"Task {task}")
    style(axes[1], "B  Fixed-input action deviation", "Relative L2 (not success rate)")
    axes[1].set_ylim(0, 1.02)
    axes[1].legend(loc="upper left")
    save(fig, "agx_latency_error.pdf")
    rows = []
    for mode, caption in [("bf16_original", "原始 BF16"), ("bf16_matched", "同优化 BF16")]:
        r = originals[mode]
        values = [f(s, "wall_ms") for s in agx_groups[mode]]
        rows.append([caption, "--", f"{f(r,'wall_median_ms'):.2f}",
                     f"{np.percentile(values,25):.2f}--{np.percentile(values,75):.2f}",
                     f"{goriginal/f(r,'wall_median_ms'):.3f}", f"{gmatched/f(r,'wall_median_ms'):.3f}"])
    for r in agx:
        rows.append(["T" + r["tier"], f"{f(r,'w4_percent'):.2f}", f"{f(r,'wall_median_ms'):.2f}",
                     f"{f(r,'p25_ms'):.2f}--{f(r,'p75_ms'):.2f}", f"{f(r,'speedup_original'):.3f}",
                     f"{f(r,'quantization_incremental_speedup'):.3f}"])
    table("agx_table.tex", "lrrrrr", ["配置", "W4A4/\\%", "延迟/ms", "P25--P75/ms", "$S_{\\rm total}$", "$S_q$"], rows)

    amap = {r["mode"]: r for r in ada}
    amatched = f(amap["bf16"], "median_ms")
    aoriginal = f(amap["original_bf16"], "median_ms")
    aq = ada[2:]
    ax = np.array([f(r, "w4_percent") for r in aq])
    ay = np.array([f(r, "median_ms") for r in aq])
    al = np.array([f(r, "p10_ms") for r in aq])
    ah = np.array([f(r, "p90_ms") for r in aq])
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 2.8), constrained_layout=True)
    axes[0].errorbar(ax, ay, yerr=[ay-al, ah-ay], fmt="o-", color=blue, capsize=2, markersize=4,
                     label="Median; P10-P90 of 10 calls")
    axes[0].axhline(amatched, color="#65758a", linestyle="--", label=f"Matched BF16: {amatched:.2f} ms")
    axes[0].axhline(aoriginal, color="#99a4b1", linestyle=":", label=f"Original BF16: {aoriginal:.2f} ms")
    style(axes[0], "A  Complete streaming plan latency", "Wall latency (ms)")
    axes[0].set_ylim(45.2, 53.4)
    axes[0].legend(loc="upper right")
    for key, color, marker, caption in [("decoded_mae_seed42", teal, "o", "MAE"),
                                        ("decoded_rmse_seed42", orange, "s", "RMSE")]:
        axes[1].plot(ax, [f(r,key) for r in aq], marker=marker, color=color, markersize=3.5, label=caption)
    style(axes[1], "B  Decoded action deviation (seed 42)", "Decoded action units")
    axes[1].set_ylim(0, .135)
    axes[1].legend(loc="upper right")
    save(fig, "ada_latency_error.pdf")
    rows = []
    for r in ada:
        caption = "同优化 BF16" if r["mode"] == "bf16" else label(r["mode"])
        rows.append([caption, r["w4_sites"] or "--", f"{f(r,'median_ms'):.3f}",
                     f"{f(r,'p10_ms'):.3f}--{f(r,'p90_ms'):.3f}", f"{f(r,'gpu_operation_ms'):.3f}",
                     f"{amatched/f(r,'median_ms'):.3f}"])
    table("ada_table.tex", "lrrrrr", ["配置", "W4A4 层", "延迟/ms", "P10--P90/ms", "GPU 工作量/ms", "$S_q$"], rows)

    # Keep the per-task heterogeneity visible without squeezing long task names into a chart.
    task_matrix = np.zeros((10,12), dtype=int)
    task_names = {}
    modes = [r["mode"] for r in thor]
    for r in tasks:
        task_matrix[int(r["task_id"]), modes.index(r["mode"])] = int(r["successes"])
        task_names[int(r["task_id"])] = r["task"]
    fig, axis = plt.subplots(figsize=(9.2, 3.1), constrained_layout=True)
    from matplotlib.colors import ListedColormap, BoundaryNorm
    cmap = ListedColormap(["#f4e6de", "#e8ecef", "#9dc5c9", "#33818e"])
    axis.imshow(task_matrix, cmap=cmap, norm=BoundaryNorm([-.5,.5,1.5,2.5,3.5],4), aspect="auto")
    for (y,x), value in np.ndenumerate(task_matrix):
        axis.text(x,y,str(value),ha="center",va="center",color="white" if value==3 else "#253144",fontsize=10)
    axis.set_xticks(range(12))
    axis.set_xticklabels([label(m) for m in modes])
    axis.set_yticks(range(10))
    axis.set_yticklabels([f"Task {i}" for i in range(10)])
    axis.set_title("Thor: successes out of the same 3 initial states per task",loc="left",fontsize=11,fontweight="bold")
    save(fig,"thor_task_heatmap.pdf")

    # Overview speedups always show their denominator and measurement scope.
    endpoint_rows=[]
    for platform, precision, orig, matched, current in [
        ("AGX Orin", "W8A8", goriginal, gmatched, gy[0]),
        ("AGX Orin", "W4A4", goriginal, gmatched, gy[-1]),
        ("RTX 6000 Ada", "W8A8", aoriginal, amatched, f(aq[0],"median_ms")),
        ("RTX 6000 Ada", "W4A4", aoriginal, amatched, f(aq[-1],"median_ms")),
        ("Thor", "FP8", None, tbase, ty[0]),
        ("Thor", "FP4", None, tbase, ty[-1]),
    ]:
        endpoint_rows.append([platform, precision, "--" if orig is None else f"{orig:.2f}",f"{matched:.2f}",
                              f"{current:.2f}", "--" if orig is None else f"{orig/current:.3f}", f"{matched/current:.3f}"])
    table("endpoints.tex", "llrrrrr",["平台","候选精度","原始 BF16","同优化 BF16","量化延迟","$S_{\\rm total}$","$S_q$"],endpoint_rows)
    for relative in [THOR / "thor_brief_report.txt", AGX.parent / "汇报.md",
                     ADA / (ADA_PREFIX + "completed_results.txt"), ADA / (ADA_PREFIX + "independent_audit.txt")]:
        INPUTS[str(relative)] = {"sha256": hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()}
    (OUT / "source_manifest.json").write_text(json.dumps({
        "inputs":INPUTS,
        "checks":"PASS: raw timing statistics, sample/visit counts, 360 paired episodes, 120 task aggregates",
        "plot_policy":"No new measurements, smoothing, inferred quality, or confidence intervals.",
        "task_names":task_names,
    },ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PASS: all plotted statistics recomputed from raw exports.")
    print("Built 4 vector figures, 4 complete tables and the source SHA256 manifest in summary/.")


if __name__ == "__main__":
    build()
