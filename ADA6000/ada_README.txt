Ada progressive quantization: intermediate results, 2026-10-13

Two-page results index: ada_progressive_report.tex
Compiler: XeLaTeX with Fandol fonts.
Original project main.tex should be preserved.

This is an intermediate-results attachment, not a complete paper. It includes
the coverage curve, DiT operator breakdown, key measured differences and a file index.
The existing measurements used piR2 11d9ddb plus the progressive patch, not a new run on 517f518.

Each configuration has 90 repeated fixed-sequence plan timings; GPU sums come
from a separate six-plan profile. These metrics must not be subtracted to infer CPU time.
The 1080-row latency CSV covers BF16 and eleven quantization tiers.
No closed-loop quality or stable best-tier claim is established.

CSV/JSON files are reusable intermediate results. The ZIP contains data, source
patch, replay scripts, dependency metadata, tactics and sanitized validation logs.
No model weights, datasets, credentials, server addresses or large traces are bundled.
Package-relative paths inside JSON resolve after extracting ada_reproducibility.zip.
