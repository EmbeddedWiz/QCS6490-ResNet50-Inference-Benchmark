#!/usr/bin/env python3

from pathlib import Path
import json
import math
import statistics


DEADLINE_US = 10_000

RUNS = [
    ("Baseline #1", "baseline", "output_baseline_2cpu/latency_us.txt"),
    ("Baseline #2", "baseline", "output_baseline_2cpu_run2/latency_us.txt"),
    ("Baseline #3", "baseline", "output_baseline_2cpu_run3/latency_us.txt"),
    ("Contention #1", "contention", "output_contention_2cpu/latency_us.txt"),
    ("Contention #2", "contention", "output_contention_2cpu_run2/latency_us.txt"),
    ("Contention #3", "contention", "output_contention_2cpu_run3/latency_us.txt"),
]


def read_latency_file(path):
    values = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            try:
                value = float(line)
            except ValueError:
                continue

            if math.isfinite(value):
                values.append(value)

    return values


def percentile(values, p):
    if not values:
        return float("nan")

    values = sorted(values)

    if len(values) == 1:
        return values[0]

    position = (len(values) - 1) * p
    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return values[lower]

    fraction = position - lower

    return (
        values[lower]
        + (values[upper] - values[lower]) * fraction
    )


def calculate_stats(values):
    if not values:
        return {
            "n": 0,
            "mean": float("nan"),
            "p50": float("nan"),
            "p95": float("nan"),
            "p99": float("nan"),
            "p999": float("nan"),
            "min": float("nan"),
            "max": float("nan"),
            "misses": 0,
        }

    return {
        "n": len(values),
        "mean": statistics.fmean(values),
        "p50": percentile(values, 0.50),
        "p95": percentile(values, 0.95),
        "p99": percentile(values, 0.99),
        "p999": percentile(values, 0.999),
        "min": min(values),
        "max": max(values),
        "misses": sum(v > DEADLINE_US for v in values),
    }


def fmt_us(value):
    if not math.isfinite(value):
        return "NaN"

    return f"{value / 1000:.3f}"


def print_stats(name, values):
    s = calculate_stats(values)

    print(
        f"{name:<18}"
        f"{s['n']:>6}"
        f"{fmt_us(s['mean']):>9}"
        f"{fmt_us(s['p50']):>9}"
        f"{fmt_us(s['p95']):>9}"
        f"{fmt_us(s['p99']):>9}"
        f"{fmt_us(s['p999']):>10}"
        f"{fmt_us(s['min']):>9}"
        f"{fmt_us(s['max']):>9}"
        f"{s['misses']:>7}"
    )


def make_run_record(name, kind, values):
    s = calculate_stats(values)

    return {
        "name": name,
        "kind": kind,
        "n": s["n"],
        "mean": s["mean"],
        "p50": s["p50"],
        "p95": s["p95"],
        "p99": s["p99"],
        "p999": s["p999"],
        "min": s["min"],
        "max": s["max"],
        "misses": s["misses"],
        "latency": values,
    }


def generate_html(root, run_records, baseline, contention):
    all_values = baseline + contention

    baseline_stats = calculate_stats(baseline)
    contention_stats = calculate_stats(contention)
    all_stats = calculate_stats(all_values)

    data = {
        "runs": run_records,
        "baseline": baseline,
        "contention": contention,
        "all": all_values,
        "deadline": DEADLINE_US,
    }

    data_json = json.dumps(
        data,
        separators=(",", ":"),
        allow_nan=False,
    )

    def js_num(value):
        if not math.isfinite(value):
            return "null"
        return str(value)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>QCS6490 ResNet-50 Inference Benchmark</title>

<style>
:root {{
    --bg: #0b1020;
    --panel: #121a2b;
    --panel2: #182238;
    --text: #e8edf7;
    --muted: #8f9bb2;
    --border: #26334d;
    --blue: #50a0ff;
    --orange: #ffa04a;
    --green: #45d483;
}}

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    background:
        radial-gradient(circle at top left, #18294b 0, transparent 35%),
        var(--bg);
    color: var(--text);
    font-family:
        Inter,
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
}}

.container {{
    max-width: 1400px;
    margin: 0 auto;
    padding: 36px 24px 60px;
}}

h1 {{
    margin: 0 0 8px;
    font-size: 32px;
}}

h2 {{
    margin: 0 0 18px;
    font-size: 21px;
}}

.subtitle {{
    color: var(--muted);
    margin-bottom: 30px;
}}

.grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 20px;
}}

.card {{
    background: rgba(18, 26, 43, 0.94);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 20px;
    box-shadow: 0 12px 35px rgba(0,0,0,.18);
}}

.metric-label {{
    color: var(--muted);
    font-size: 13px;
    margin-bottom: 8px;
}}

.metric {{
    font-size: 28px;
    font-weight: 700;
}}

.metric-small {{
    color: var(--muted);
    font-size: 13px;
    margin-top: 5px;
}}

section {{
    margin-top: 20px;
}}

.chart-card {{
    background: rgba(18, 26, 43, 0.94);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 22px;
}}

canvas {{
    width: 100%;
    height: 360px;
    display: block;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
}}

th {{
    text-align: right;
    color: var(--muted);
    font-weight: 500;
    padding: 12px 8px;
    border-bottom: 1px solid var(--border);
}}

th:first-child,
td:first-child {{
    text-align: left;
}}

td {{
    text-align: right;
    padding: 12px 8px;
    border-bottom: 1px solid #202c43;
}}

.baseline {{
    color: var(--blue);
}}

.contention {{
    color: var(--orange);
}}

.note {{
    color: var(--muted);
    line-height: 1.6;
}}

.footer {{
    margin-top: 30px;
    color: var(--muted);
    font-size: 13px;
}}

@media (max-width: 1000px) {{
    .grid {{
        grid-template-columns: repeat(2, 1fr);
    }}
}}

@media (max-width: 600px) {{
    .container {{
        padding: 20px 12px 40px;
    }}

    .grid {{
        grid-template-columns: 1fr;
    }}

    table {{
        font-size: 11px;
    }}
}}
</style>
</head>

<body>
<div class="container">

<h1>QCS6490 ResNet-50 Inference Benchmark</h1>

<div class="subtitle">
Qualcomm QNN / Hexagon HTP latency benchmark ·
3 baseline runs + 3 CPU-contention runs ·
1000 inferences per run
</div>

<div class="grid">

<div class="card">
    <div class="metric-label">Measurements</div>
    <div class="metric">{len(all_values):,}</div>
    <div class="metric-small">
        {len(baseline):,} baseline · {len(contention):,} contention
    </div>
</div>

<div class="card">
    <div class="metric-label">Baseline mean</div>
    <div class="metric">{fmt_us(baseline_stats["mean"])} ms</div>
    <div class="metric-small">
        P99 {fmt_us(baseline_stats["p99"])} ms
    </div>
</div>

<div class="card">
    <div class="metric-label">Contention mean</div>
    <div class="metric">{fmt_us(contention_stats["mean"])} ms</div>
    <div class="metric-small">
        P99 {fmt_us(contention_stats["p99"])} ms
    </div>
</div>

<div class="card">
    <div class="metric-label">Deadline misses</div>
    <div class="metric">{all_stats["misses"]}</div>
    <div class="metric-small">
        Deadline: {DEADLINE_US / 1000:.1f} ms
    </div>
</div>

</div>

<section class="chart-card">
<h2>Latency over all {len(all_values):,} measurements</h2>
<canvas id="latencyChart"></canvas>
</section>

<section class="chart-card">
<h2>Latency distribution</h2>
<canvas id="histogram"></canvas>
</section>

<section class="card">
<h2>Run statistics</h2>

<table>
<thead>
<tr>
<th>Run</th>
<th>N</th>
<th>Mean ms</th>
<th>P50 ms</th>
<th>P95 ms</th>
<th>P99 ms</th>
<th>P99.9 ms</th>
<th>Min ms</th>
<th>Max ms</th>
<th>&gt;10 ms</th>
</tr>
</thead>
<tbody id="runTable"></tbody>
</table>
</section>

<section class="card">
<h2>Interpretation</h2>

<p class="note">
Under the tested workload and system configuration, CPU contention on
two host CPUs did not produce a measurable latency degradation of the
QNN ResNet-50 inference path. The baseline itself shows run-to-run
variability, so the lower latency observed during contention should not
be interpreted as a performance improvement.
</p>

<p class="note">
The experiment evaluates this specific QCS6490/QNN workload,
configuration and contention pattern. It is not a general
characterization of QNN, Hexagon HTP or QCS6490 performance under
arbitrary workloads.
</p>
</section>

<div class="footer">
Generated from the six completed benchmark runs.
</div>

</div>

<script>
const DATA = {data_json};

function ms(v) {{
    return (v / 1000).toFixed(3);
}}

function drawLatency() {{
    const canvas = document.getElementById("latencyChart");
    const ctx = canvas.getContext("2d");

    const values = DATA.all;

    const width = canvas.clientWidth * devicePixelRatio;
    const height = 360 * devicePixelRatio;

    canvas.width = width;
    canvas.height = height;

    ctx.clearRect(0, 0, width, height);

    const pad = 42 * devicePixelRatio;
    const innerW = width - pad * 2;
    const innerH = height - pad * 2;

    const maxValue = Math.max(...values, DATA.deadline);
    const minValue = Math.min(...values);

    function x(i) {{
        return pad + i / (values.length - 1) * innerW;
    }}

    function y(v) {{
        return height - pad -
            (v - minValue) / (maxValue - minValue) * innerH;
    }}

    ctx.strokeStyle = "#26334d";
    ctx.lineWidth = 1;

    for (let i = 0; i <= 4; i++) {{
        const yy = pad + i / 4 * innerH;

        ctx.beginPath();
        ctx.moveTo(pad, yy);
        ctx.lineTo(width - pad, yy);
        ctx.stroke();
    }}

    ctx.strokeStyle = "#50a0ff";
    ctx.lineWidth = 1.2 * devicePixelRatio;

    ctx.beginPath();

    values.forEach((v, i) => {{
        if (i === 0) {{
            ctx.moveTo(x(i), y(v));
        }} else {{
            ctx.lineTo(x(i), y(v));
        }}
    }});

    ctx.stroke();

    const deadlineY = y(DATA.deadline);

    ctx.strokeStyle = "#ffa04a";
    ctx.setLineDash([8 * devicePixelRatio, 6 * devicePixelRatio]);

    ctx.beginPath();
    ctx.moveTo(pad, deadlineY);
    ctx.lineTo(width - pad, deadlineY);
    ctx.stroke();

    ctx.setLineDash([]);

    ctx.fillStyle = "#8f9bb2";
    ctx.font = `${{12 * devicePixelRatio}}px system-ui`;

    ctx.fillText(
        "0",
        8 * devicePixelRatio,
        height - pad
    );

    ctx.fillText(
        maxValue / 1000 .toFixed
            ? (maxValue / 1000).toFixed(1) + " ms"
            : "",
        8 * devicePixelRatio,
        pad
    );

    ctx.fillStyle = "#ffa04a";
    ctx.fillText(
        "deadline 10 ms",
        width - 105 * devicePixelRatio,
        deadlineY - 7 * devicePixelRatio
    );
}}

function drawHistogram() {{
    const canvas = document.getElementById("histogram");
    const ctx = canvas.getContext("2d");

    const width = canvas.clientWidth * devicePixelRatio;
    const height = 360 * devicePixelRatio;

    canvas.width = width;
    canvas.height = height;

    ctx.clearRect(0, 0, width, height);

    const pad = 42 * devicePixelRatio;
    const innerW = width - pad * 2;
    const innerH = height - pad * 2;

    const values = DATA.all;

    const min = Math.min(...values);
    const max = Math.max(...values);

    const bins = 40;
    const counts = new Array(bins).fill(0);

    values.forEach(v => {{
        let index =
            Math.floor((v - min) / (max - min) * bins);

        if (index >= bins) index = bins - 1;
        if (index < 0) index = 0;

        counts[index]++;
    }});

    const maxCount = Math.max(...counts);

    for (let i = 0; i < bins; i++) {{
        const barW = innerW / bins;
        const barH = counts[i] / maxCount * innerH;

        const x = pad + i * barW;
        const y = height - pad - barH;

        ctx.fillStyle =
            i < bins / 2
                ? "rgba(80,160,255,0.65)"
                : "rgba(255,160,70,0.65)";

        ctx.fillRect(
            x,
            y,
            Math.max(1, barW - 1),
            barH
        );
    }}

    const deadlineX =
        pad +
        (DATA.deadline - min) /
        (max - min) *
        innerW;

    ctx.strokeStyle = "#ffa04a";
    ctx.setLineDash([8 * devicePixelRatio, 6 * devicePixelRatio]);
    ctx.lineWidth = 2 * devicePixelRatio;

    ctx.beginPath();
    ctx.moveTo(deadlineX, pad);
    ctx.lineTo(deadlineX, height - pad);
    ctx.stroke();

    ctx.setLineDash([]);

    ctx.fillStyle = "#8f9bb2";
    ctx.font = `${{12 * devicePixelRatio}}px system-ui`;

    ctx.fillText(
        min / 1000 .toFixed
            ? (min / 1000).toFixed(1) + " ms"
            : "",
        pad,
        height - 10 * devicePixelRatio
    );

    ctx.fillText(
        max / 1000 .toFixed
            ? (max / 1000).toFixed(1) + " ms"
            : "",
        width - 75 * devicePixelRatio,
        height - 10 * devicePixelRatio
    );
}}

function fillTable() {{
    const tbody = document.getElementById("runTable");

    DATA.runs.forEach(run => {{
        const tr = document.createElement("tr");

        tr.className = run.kind;

        tr.innerHTML = `
            <td>${{run.name}}</td>
            <td>${{run.n}}</td>
            <td>${{ms(run.mean)}}</td>
            <td>${{ms(run.p50)}}</td>
            <td>${{ms(run.p95)}}</td>
            <td>${{ms(run.p99)}}</td>
            <td>${{ms(run.p999)}}</td>
            <td>${{ms(run.min)}}</td>
            <td>${{ms(run.max)}}</td>
            <td>${{run.misses}}</td>
        `;

        tbody.appendChild(tr);
    }});
}}

fillTable();
drawLatency();
drawHistogram();

window.addEventListener("resize", () => {{
    drawLatency();
    drawHistogram();
}});
</script>

</body>
</html>
"""

    output = root / "resnet50_report.html"

    output.write_text(
        html,
        encoding="utf-8"
    )

    return output


def main():
    root = Path.cwd()

    print()
    print("QCS6490 ResNet-50 / QNN latency analysis")
    print("=" * 110)
    print()
    print(
        f"{'Run':<18}"
        f"{'N':>6}"
        f"{'Mean':>9}"
        f"{'P50':>9}"
        f"{'P95':>9}"
        f"{'P99':>9}"
        f"{'P99.9':>10}"
        f"{'Min':>9}"
        f"{'Max':>9}"
        f"{'>10ms':>7}"
    )
    print("-" * 110)

    baseline = []
    contention = []
    run_records = []

    for name, kind, relative_path in RUNS:
        path = root / relative_path

        if not path.exists():
            print()
            print(f"ERROR: missing latency file: {path}")
            raise SystemExit(1)

        values = read_latency_file(path)

        if not values:
            print()
            print(f"ERROR: latency file is empty: {path}")
            raise SystemExit(1)

        print_stats(name, values)

        record = make_run_record(
            name,
            kind,
            values
        )

        run_records.append(record)

        if kind == "baseline":
            baseline.extend(values)
        else:
            contention.extend(values)

    print("-" * 110)

    print_stats(
        "Baseline TOTAL",
        baseline
    )

    print_stats(
        "Contention TOTAL",
        contention
    )

    print("-" * 110)

    all_values = baseline + contention

    print_stats(
        "ALL MEASUREMENTS",
        all_values
    )

    print()
    print(f"Baseline measurements  : {len(baseline)}")
    print(f"Contention measurements: {len(contention)}")
    print(f"Total measurements     : {len(all_values)}")
    print(f"Deadline               : {DEADLINE_US / 1000:.1f} ms")

    output = generate_html(
        root,
        run_records,
        baseline,
        contention
    )

    print()
    print("HTML report written to:")
    print(output)
    print()


if __name__ == "__main__":
    main()
