#!/usr/bin/env python3

import csv
import statistics
import sys
from pathlib import Path


def percentile(values, p):
    if not values:
        return 0.0

    values = sorted(values)

    if len(values) == 1:
        return values[0]

    position = (len(values) - 1) * p
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    fraction = position - lower

    return values[lower] + (values[upper] - values[lower]) * fraction


def extract(profile_csv, output_csv):
    values = []

    with open(profile_csv, newline="") as f:
        reader = csv.reader(f)

        for row in reader:
            if len(row) < 7:
                continue

            # qnn-profile-viewer format:
            # Timestamp, Event, Time, Unit, Component, Subcomponent, EventName

            try:
                event = row[1]
                value = float(row[2])
                unit = row[3]
                component = row[4]
                subcomponent = row[5]
                event_name = row[6]
            except (ValueError, IndexError):
                continue

            if (
                event == "EXECUTE"
                and unit == "US"
                and component == "NETRUN"
                and subcomponent == "ROOT"
                and event_name.startswith("Graph 0:")
            ):
                values.append(value)

    if not values:
        raise RuntimeError(
            f"No NETRUN Graph EXECUTE latency records found in {profile_csv}"
        )

    with open(output_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["inference", "latency_us"])

        for index, value in enumerate(values, start=1):
            writer.writerow([index, f"{value:.3f}"])

    mean = statistics.fmean(values)

    summary = {
        "count": len(values),
        "mean_us": mean,
        "p50_us": percentile(values, 0.50),
        "p95_us": percentile(values, 0.95),
        "p99_us": percentile(values, 0.99),
        "p99_9_us": percentile(values, 0.999),
        "min_us": min(values),
        "max_us": max(values),
        "over_10ms": sum(v > 10000.0 for v in values),
    }

    return summary


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(
            f"Usage: {sys.argv[0]} PROFILE_CSV OUTPUT_CSV",
            file=sys.stderr,
        )
        sys.exit(2)

    result = extract(Path(sys.argv[1]), Path(sys.argv[2]))

    print(f"count     : {result['count']}")
    print(f"mean      : {result['mean_us'] / 1000:.3f} ms")
    print(f"P50       : {result['p50_us'] / 1000:.3f} ms")
    print(f"P95       : {result['p95_us'] / 1000:.3f} ms")
    print(f"P99       : {result['p99_us'] / 1000:.3f} ms")
    print(f"P99.9     : {result['p99_9_us'] / 1000:.3f} ms")
    print(f"min       : {result['min_us'] / 1000:.3f} ms")
    print(f"max       : {result['max_us'] / 1000:.3f} ms")
    print(f">10 ms    : {result['over_10ms']}")
