# Benchmark Environment Setup

This document describes the exact software environment used for the QCS6490 ResNet-50 benchmark on the Dragon Q6A.

It is intentionally specific to this project and is not a generic QNN/QAIRT installation guide.

## Target

- Board: Qualcomm QCS6490 / Radxa Dragon Q6A
- Host OS: the Linux environment running on the Q6A
- QNN / QAIRT: **2.37.1.250807**
- HTP backend: `libQnnHtp.so`
- Model context: `resnet50_aimet_quantized_6490.bin`
- Input list: `test_list.txt`
- QNN inference CPUs: `4,5`
- Inferences per run: `1000`

## Required files already present on the Q6A

The benchmark uses the existing ResNet-50 QNN artifact directory:

```text
~/Projects/q6a-ai-demo_hu/resnet50_qairt/6490
```

This directory provides the QNN executable, HTP backend, context and input list used by the benchmark:

```text
qnn-net-run
libQnnHtp.so
resnet50_aimet_quantized_6490.bin
test_list.txt
```

The matching QNN profile viewer is taken from:

```text
~/qnn-tools/2.37.1.250807/bin/qnn-profile-viewer
```

Do not replace these files with the QNN 2.47.0 environment used by the separate `LiteRT-Embedded-Inference` project.

## Configure the project

From the repository root:

```bash
cd ~/Projects/qcs6490-resnet50-inference-benchmark
```

Create or update `config/local.conf` with the exact paths used on the Q6A:

```bash
cat > config/local.conf <<'EOF2'
QNN_ARTIFACT_DIR="/home/radxa/Projects/q6a-ai-demo_hu/resnet50_qairt/6490"
QNN_PROFILE_VIEWER="/home/radxa/qnn-tools/2.37.1.250807/bin/qnn-profile-viewer"

QNN_BACKEND="libQnnHtp.so"
QNN_CONTEXT="resnet50_aimet_quantized_6490.bin"
QNN_INPUT_LIST="test_list.txt"

CPU_LIST="4,5"
INFERENCES=1000
EOF2
```

`config/local.conf` is machine-specific and is not part of the portable benchmark configuration.

## Verify the required files

Run:

```bash
test -x /home/radxa/Projects/q6a-ai-demo_hu/resnet50_qairt/6490/qnn-net-run
test -f /home/radxa/Projects/q6a-ai-demo_hu/resnet50_qairt/6490/libQnnHtp.so
test -f /home/radxa/Projects/q6a-ai-demo_hu/resnet50_qairt/6490/resnet50_aimet_quantized_6490.bin
test -f /home/radxa/Projects/q6a-ai-demo_hu/resnet50_qairt/6490/test_list.txt
test -x /home/radxa/qnn-tools/2.37.1.250807/bin/qnn-profile-viewer
```

The benchmark was run with matching QNN 2.37.1.250807 versions of `qnn-net-run`, `qnn-profile-viewer` and the HTP backend.

## Build the local stressor

The CPU contention experiment uses the stressor included in this repository:

```bash
make -C stressor
```

The resulting executable is:

```text
stressor/cpu-stressor-affinity
```

## Run

After the environment is prepared:

```bash
./scripts/run_benchmark.sh
```

The script performs three baseline runs and three CPU-contention runs, with 1000 inferences per run.

## Important reproducibility point

This project deliberately uses the exact QNN 2.37.1.250807 environment above. Do not mix its QNN binaries, HTP libraries, model context or profiling tools with the QNN 2.47.0 files used by the separate `LiteRT-Embedded-Inference` project.
