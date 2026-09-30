# QCS6490 ResNet-50 Inference Benchmark

Determinism and latency benchmark for ResNet-50 inference on the Qualcomm QCS6490 Dragon Q6A platform using Qualcomm QNN / QAIRT with the Hexagon HTP (NPU) backend.

The benchmark measures per-inference latency and compares two execution conditions:

* **Baseline** — normal system operation.
* **CPU contention** — the inference workload runs while two host CPUs are deliberately stressed.

The purpose is to evaluate latency, jitter and deadline behavior of the complete QNN inference path under a controlled host-CPU load.

## Benchmark Report

[View the interactive benchmark report →](https://htmlpreview.github.io/?https://raw.githubusercontent.com/EmbeddedWiz/QCS6490-ResNet50-Inference-Benchmark/main/report/resnet50_report.html)

## Platform and workload

* **Target:** Qualcomm QCS6490 / Dragon Q6A
* **Inference backend:** Qualcomm QNN / QAIRT
* **QNN version:** 2.37.1.250807
* **Accelerator:** Hexagon HTP / NPU
* **Model:** ResNet-50
* **Input:** 224×224 RAW
* **Inferences per run:** 1000
* **Runs:** 3 baseline + 3 CPU-contention
* **Total measurements:** 6000
* **CPU affinity:** CPUs 4,5
* **QNN profiling:** detailed
* **Deadline:** 10 ms

The benchmark uses a pre-generated quantized ResNet-50 QNN context for the QCS6490 HTP backend:

```text
resnet50_aimet_quantized_6490.bin
```

The exact verified environment used for the measurements is documented in [`environment.md`](environment.md).

## Measurement method

Each run executes 1000 consecutive QNN inferences. Detailed QNN profiling is enabled and the `NETRUN / ROOT / Graph 0` `EXECUTE` events are extracted as the per-inference latency samples.

The `Time` field of these events represents the complete application-visible inference latency reported by QNN NetRun. Nested RPC, accelerator and backend events are not summed together because they are components of the same execution path.

The raw samples are preserved in execution order. No smoothing or filtering is applied to the measured latency values used for the statistics.

For each run the benchmark reports:

* Mean
* P50
* P95
* P99
* P99.9
* Minimum
* Maximum
* Number of deadline misses above 10 ms

The final report also provides combined statistics for the baseline and contention datasets and a latency-over-time visualization.

## Experimental conditions

### Baseline

The ResNet-50 inference workload runs without the artificial CPU stressor.

### CPU contention

The same inference workload runs while two host CPUs are loaded by the CPU stressor included in this repository.

CPU affinity is explicit rather than left entirely to the scheduler:

* The QNN inference process is pinned with `taskset -c "$CPU_LIST"`, using the CPU set defined by the benchmark configuration.
* The contention stressor uses its affinity-aware launcher and is pinned to its configured CPU set through the `cpu-stressor-affinity` / `main_affinity.cpp` path.

The tested CPU set is:

```text
4,5
```

This keeps the inference workload and the CPU stressor on controlled host-CPU sets instead of allowing their placement to vary freely from run to run. The exact CPU sets are taken from the experiment configuration and should be kept unchanged when reproducing the benchmark.

The contention experiment is intended to test whether host-CPU activity causes additional latency or jitter in the QNN/HTP inference path.

## Observed results

The completed benchmark contains 6000 individual inference measurements:

* 3000 baseline measurements;
* 3000 CPU-contention measurements.

The combined results are:

| Condition      | N    | Mean     | P50      | P95      | P99      | P99.9    | Min      | Max      | >10 ms |
| -------------- | ---: | -------: | -------: | -------: | -------: | -------: | -------: | -------: | -----: |
| Baseline       | 3000 | 4.223 ms | 4.065 ms | 5.036 ms | 5.493 ms | 6.890 ms | 3.584 ms | 7.902 ms | 0 |
| CPU contention | 3000 | 4.228 ms | 3.994 ms | 4.986 ms | 5.122 ms | 6.386 ms | 3.619 ms | 7.146 ms | 0 |

Across all 6000 measurements:

| Metric | Result |
| ------ | -----: |
| Mean | 4.225 ms |
| P50 | 4.023 ms |
| P95 | 4.991 ms |
| P99 | 5.423 ms |
| P99.9 | 6.752 ms |
| Minimum | 3.584 ms |
| Maximum | 7.902 ms |
| Samples above 10 ms | 0 |

The difference between the combined baseline and contention means is approximately **0.005 ms (5 µs)**.

Under the tested configuration, CPU contention on the two selected host CPUs therefore produced **no measurable latency degradation** of the QNN/HTP inference path at the scale of this experiment.

The result should not be interpreted as proof that host-CPU contention can never affect QNN or HTP performance. It is an observation specific to this platform, software stack, workload, CPU affinity and contention pattern.

## QNN execution and end-to-end latency

The benchmark measures application-visible end-to-end inference latency rather than accelerator execution time alone.

QNN detailed profiling exposes several nested timing components, including:

* NetRun execution time;
* RPC execution time;
* QNN accelerator execution time;
* VTCM acquisition;
* HVX/HMX power acquisition;
* accelerator execution;
* accelerator execution excluding wait.

For the tested ResNet-50 context, the HTP backend reported:

```text
Number of HVX threads used: 4
```

Typical accelerator execution is around 2 ms, while the complete NetRun inference latency is around 4 ms. The difference represents host/runtime and synchronization overheads in the complete inference path rather than accelerator computation alone.

This distinction is important when evaluating deterministic AI execution: optimizing accelerator execution time does not necessarily reduce the complete application-visible latency by the same amount.

## Repository layout

```text
qcs6490-resnet50-inference-benchmark/
├── config/
│   ├── experiment.conf
│   └── local.conf
├── docs/
│   ├── environment.md
│   └── methodology.md
├── report/
│   └── resnet50_report.html
├── results/
│   ├── baseline/
│   │   ├── run1/
│   │   ├── run2/
│   │   └── run3/
│   └── contention/
│       ├── run1/
│       ├── run2/
│       └── run3/
├── scripts/
│   ├── analyze_results.py
│   ├── extract_latency.py
│   ├── run_benchmark.sh
│   ├── serve_report.sh
│   └── setup.sh
├── stressor/
│   ├── cpu-stressor-affinity
│   ├── main_affinity.cpp
│   └── Makefile
├── tools/
│   └── termo2
└── README.md
```

## Running the benchmark

Configure the machine-specific environment in `config/local.conf`.

The benchmark used for the measurements in this repository was run with the verified QNN 2.37.1.250807 environment described in [`environment.md`](environment.md).

Build the CPU stressor if necessary:

```bash
make -C stressor
```

Run the complete benchmark:

```bash
./scripts/run_benchmark.sh
```

The benchmark performs:

1. three baseline runs;
2. three CPU-contention runs;
3. detailed QNN profiling for every run;
4. extraction of per-inference latency;
5. generation of the HTML report.

The benchmark stores the raw profiling output and extracted latency samples under `results/`.

The HTML report is generated at:

```text
report/resnet50_report.html
```

For local viewing, the repository provides:

```bash
./scripts/serve_report.sh
```

The `setup.sh` script is retained in the repository, but the measurements documented here were performed using the exact verified environment described in `environment.md` rather than a generic QNN installation procedure.

## Raw measurement data

Each run contains the following important files:

```text
profile.csv
latency.csv
latency_us.txt
qnn-profiling-data_0.log
```

`latency.csv` preserves the per-inference sequence:

```text
inference,latency_us
1,5992.000
2,4121.000
3,3968.000
...
```

`latency_us.txt` contains the latency samples used by the report generator.

The original QNN profiling data is retained so that the reported statistics can be independently checked or reprocessed.

## Interpretation

This benchmark is a controlled experiment, not a general characterization of the QCS6490, QNN, QAIRT or Hexagon HTP under arbitrary workloads.

The result applies only to the tested:

* hardware platform;
* firmware and operating-system state;
* QNN / QAIRT software stack;
* ResNet-50 model and input;
* inference configuration;
* CPU affinity and stressor configuration;
* measurement procedure.

The experiment did not show a measurable latency degradation when two selected host CPUs were deliberately stressed. This does not establish that CPU contention is irrelevant to QNN/HTP performance in general. Different CPU sets, workloads, power states, background activity, models, scheduling conditions or system configurations can produce different results.

## Reproducibility

For reproducible measurements, keep the following fixed between runs:

* model and input data;
* QNN backend and context;
* QNN / QAIRT version;
* number of inferences;
* CPU affinity;
* contention configuration;
* profiling level;
* software and firmware versions;
* benchmark procedure.

The exact environment used for the documented measurements is recorded in [`environment.md`](environment.md).

Repeated runs are intentionally retained so that run-to-run variability can be inspected rather than hidden by averaging alone.

## License

See [`LICENSE`](LICENSE).
