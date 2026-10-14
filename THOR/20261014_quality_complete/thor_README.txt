Thor progressive scan: completed 360-episode pilot

Start with thor_brief_report.txt, thor_progressive_complete.png and thor_quality_complete.png.
The matching PDFs are vector figures, not papers or standalone report PDFs.
Use thor_figure.tex to include the figures from this folder in Overleaf.

New complete results:
- thor_quality_modes_12.csv: 12 complete 30-episode configurations; descriptive success rates, percentage-point deltas, and paired wins/losses versus BF16.
- thor_quality_tasks_120.csv: successes out of 3 for every configuration/task; full task names.
- thor_quality_episodes_360.csv: one row per mode/task/initial state, matched BF16 outcome, steps, timing diagnostics, initialization fingerprints and source-ledger digests.
- thor_performance_quality_complete.csv: the existing observed-3200 performance and complete quality results joined by exact configuration.

The 12-mode pilot completed at 2026-10-14 02:05:19 China time. Each mode uses the same 10 tasks x 3 fixed initial states. This replaces the 193/360 intermediate quality snapshot; completion is not quality acceptance or quantization equivalence. Fixed-delay 20 Hz quality (visual 3/action 1 ticks) is separate from wall-clock deployment evaluation.

Unchanged performance: thor_progressive_performance.* and thor_progressive_latency_zh.png; thor_observed3200_summary.csv; thor_clean_samples_360.csv; thor_profiles_180.csv; thor_dummy_profiles_36_excluded.csv; thor_measured_precision_map_2112.csv; thor_configurations.json. All are byte-identical to the reviewed previous export. The main curve includes only eligible observed-3200 MHz samples, not all 360 clean/180 profiles. No clocks were changed.

thor_provenance.json records the source/config/checkpoint/input hashes, timing boundaries, quality protocol, audit checks and source-ledger digests. thor_manifest.json covers every exported attachment. Relative ledger paths identify local evidence, which is retained outside this upload. Episode record hashes use canonical sorted-key compact UTF-8 JSON as specified in provenance.

No pending quality values, no inferred accuracy, no smooth/monotonic fit. No model, observation tensor/image, large trace, private host/path or credential is included. No PR update.
