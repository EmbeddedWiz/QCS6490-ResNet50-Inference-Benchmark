#!/usr/bin/env bash

set -u -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

LOCAL_CONFIG="$PROJECT_ROOT/config/local.conf"

if [[ ! -f "$LOCAL_CONFIG" ]]; then
    echo "ERROR: local configuration does not exist."
    echo "Run:"
    echo "  ./scripts/setup.sh"
    exit 1
fi

# shellcheck disable=SC1091
source "$LOCAL_CONFIG"

RESULTS_DIR="$PROJECT_ROOT/results"
REPORT_DIR="$PROJECT_ROOT/report"
STRESSOR="$PROJECT_ROOT/stressor/cpu-stressor-affinity"
ANALYZER="$PROJECT_ROOT/scripts/analyze_results.py"
EXTRACTOR="$PROJECT_ROOT/scripts/extract_latency.py"

BASELINE_DIR="$RESULTS_DIR/baseline"
CONTENTION_DIR="$RESULTS_DIR/contention"

mkdir -p "$RESULTS_DIR" "$REPORT_DIR"

echo
echo "============================================================"
echo " QCS6490 ResNet-50 Inference Benchmark"
echo "============================================================"
echo
echo "QNN artifacts : $QNN_ARTIFACT_DIR"
echo "CPUs          : $CPU_LIST"
echo "Inferences    : $INFERENCES per run"
echo

rm -rf "$BASELINE_DIR" "$CONTENTION_DIR"
mkdir -p "$BASELINE_DIR" "$CONTENTION_DIR"

rm -f \
    "$PROJECT_ROOT/output_baseline_2cpu" \
    "$PROJECT_ROOT/output_baseline_2cpu_run2" \
    "$PROJECT_ROOT/output_baseline_2cpu_run3" \
    "$PROJECT_ROOT/output_contention_2cpu" \
    "$PROJECT_ROOT/output_contention_2cpu_run2" \
    "$PROJECT_ROOT/output_contention_2cpu_run3"

rm -f "$REPORT_DIR/resnet50_report.html"

STRESSOR_PID=""

cleanup_stressor()
{
    if [[ -n "${STRESSOR_PID:-}" ]]; then
        if kill -0 "$STRESSOR_PID" 2>/dev/null; then
            kill "$STRESSOR_PID" 2>/dev/null || true
        fi

        wait "$STRESSOR_PID" 2>/dev/null || true
        STRESSOR_PID=""
    fi
}

trap cleanup_stressor EXIT INT TERM


run_qnn()
{
    local run_dir="$1"

    mkdir -p "$run_dir"

    (
        cd "$QNN_ARTIFACT_DIR" || exit 1

        export LD_LIBRARY_PATH="$QNN_ARTIFACT_DIR:${LD_LIBRARY_PATH:-}"

        taskset -c "$CPU_LIST" \
            ./qnn-net-run \
            --backend "./$QNN_BACKEND" \
            --retrieve_context "./$QNN_CONTEXT" \
            --input_list "./$QNN_INPUT_LIST" \
            --output_dir "$run_dir" \
            --profiling_level=detailed \
            --num_inferences="$INFERENCES"
    )
}


profile_run()
{
    local run_dir="$1"

    echo "Generating QNN profile CSV..."

    "$QNN_PROFILE_VIEWER" \
        --input_log "$run_dir/qnn-profiling-data_0.log" \
        --output "$run_dir/profile.csv"

    echo "Extracting per-inference latency..."

    python3 "$EXTRACTOR" \
        "$run_dir/profile.csv" \
        "$run_dir/latency.csv"

    echo "Creating report-generator latency file..."

    tail -n +2 "$run_dir/latency.csv" |
        cut -d',' -f2 |
        sed '/^[[:space:]]*$/d' \
        > "$run_dir/latency_us.txt"

    local count

    count=$(wc -l < "$run_dir/latency_us.txt")

    echo "Latency samples: $count"

    if [[ "$count" -eq 0 ]]; then
        echo "ERROR: no latency samples extracted."
        exit 1
    fi
}


run_one()
{
    local mode="$1"
    local number="$2"
    local run_dir="$3"

    echo
    echo "------------------------------------------------------------"
    echo "$mode #$number"
    echo "------------------------------------------------------------"
    echo

    if [[ "$mode" == "Contention" ]]; then
        echo "Starting CPU contention stressor..."

        "$STRESSOR" &
        STRESSOR_PID=$!

        sleep 1
    fi

    echo "Running $INFERENCES QNN inferences..."

    if run_qnn "$run_dir"; then
        :
    else
        status=$?

        cleanup_stressor

        echo "ERROR: qnn-net-run failed for $mode #$number (status $status)"

        exit "$status"
    fi

    cleanup_stressor

    profile_run "$run_dir"

    echo
    echo "$mode #$number complete."
}


run_one "Baseline" 1 "$BASELINE_DIR/run1"
run_one "Baseline" 2 "$BASELINE_DIR/run2"
run_one "Baseline" 3 "$BASELINE_DIR/run3"

run_one "Contention" 1 "$CONTENTION_DIR/run1"
run_one "Contention" 2 "$CONTENTION_DIR/run2"
run_one "Contention" 3 "$CONTENTION_DIR/run3"


echo
echo "============================================================"
echo "Preparing report input paths"
echo "============================================================"

ln -s "$BASELINE_DIR/run1" \
    "$PROJECT_ROOT/output_baseline_2cpu"

ln -s "$BASELINE_DIR/run2" \
    "$PROJECT_ROOT/output_baseline_2cpu_run2"

ln -s "$BASELINE_DIR/run3" \
    "$PROJECT_ROOT/output_baseline_2cpu_run3"

ln -s "$CONTENTION_DIR/run1" \
    "$PROJECT_ROOT/output_contention_2cpu"

ln -s "$CONTENTION_DIR/run2" \
    "$PROJECT_ROOT/output_contention_2cpu_run2"

ln -s "$CONTENTION_DIR/run3" \
    "$PROJECT_ROOT/output_contention_2cpu_run3"


echo
echo "Generating HTML report..."

(
    cd "$PROJECT_ROOT" || exit 1

    python3 "$ANALYZER"
)

if [[ ! -f "$PROJECT_ROOT/resnet50_report.html" ]]; then
    echo "ERROR: report generator did not create resnet50_report.html"
    exit 1
fi

mv -f \
    "$PROJECT_ROOT/resnet50_report.html" \
    "$REPORT_DIR/resnet50_report.html"


echo
echo "============================================================"
echo "Benchmark complete."
echo "============================================================"
echo
echo "Report:"
echo "  $REPORT_DIR/resnet50_report.html"
echo
echo "Serve on Q6A:"
echo "  ./scripts/serve_report.sh"
echo
echo "SSH port forwarding from workstation:"
echo "  ssh -L 8000:127.0.0.1:8000 radxa@radxa-dragon-q6a"
echo
echo "Then open:"
echo "  http://127.0.0.1:8000/resnet50_report.html"
echo
