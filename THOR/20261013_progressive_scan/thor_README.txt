Thor 渐进量化中间结果
先看 thor_brief_report.txt、thor_progressive_performance.png 和 thor_observed3200_summary.csv。
thor_progressive_latency_zh.png 是独立中文延迟曲线；thor_progressive_performance.pdf 为矢量图，不是论文或报告 PDF。
thor_figure.tex 是可选插图片段，图文件在同目录时可直接引用。
主图仅使用观测 EMC 3200 MHz 子集；360 clean / 180 profiles 是未按频率筛选的完整扫描量，不能当成图上有效样本数。
CSV：thor_clean_samples_360.csv（全部clean）、thor_profiles_180.csv（正式profile）、thor_dummy_profiles_36_excluded.csv（不入统计）。
thor_measured_precision_map_2112.csv 来自11档×192层的实际运行记录，各档3次访问一致。
thor_quality_snapshot_193of360.csv 冻结于北京时间2026-10-13 23:38:59，不能当成上传时最新进度。
thor_configurations.json / thor_provenance.json 保存配置、计时口径、环境、源版本、模型与输入哈希；thor_manifest.json 校验本包附件。
GPU工作量与单次wall延迟分开；没有任务质量等价或全模型量化结论。
本包不含模型、图像/观测张量、原始大trace、主机地址、私人目录或凭据，也不包含论文正文。
