
#include <atomic>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <pthread.h>
#include <sched.h>
#include <thread>
#include <vector>

std::atomic<bool> stop_requested{false};

void cpu_worker(int worker_id, int cpu)
{
    cpu_set_t cpuset;

    CPU_ZERO(&cpuset);
    CPU_SET(cpu, &cpuset);

    int ret = pthread_setaffinity_np(
        pthread_self(),
        sizeof(cpu_set_t),
        &cpuset
    );

    if (ret != 0) {
        std::printf(
            "Worker %d: pthread_setaffinity_np failed, error = %d\n",
            worker_id,
            ret
        );
        return;
    }

    int actual_cpu = sched_getcpu();

    std::printf(
        "Worker %d started: requested CPU %d, actual CPU %d\n",
        worker_id,
        cpu,
        actual_cpu
    );

    volatile std::uint64_t value = worker_id + 1;

    while (!stop_requested.load(std::memory_order_relaxed)) {
        value = value * 1664525ULL + 1013904223ULL;
        value ^= value >> 13;
        value += 0x9e3779b97f4a7c15ULL;
    }

    actual_cpu = sched_getcpu();

    std::printf(
        "Worker %d finished on CPU %d, value = %llu\n",
        worker_id,
        actual_cpu,
        static_cast<unsigned long long>(value)
    );
}

int main()
{
    constexpr int worker_count = 2;

    const int cpus[worker_count] = {
        4, 5,
    };

    std::vector<std::thread> workers;

    for (int i = 0; i < worker_count; ++i) {
        workers.emplace_back(cpu_worker, i, cpus[i]);
    }

    std::this_thread::sleep_for(std::chrono::seconds(10));

    stop_requested.store(true, std::memory_order_relaxed);

    for (auto& worker : workers) {
        worker.join();
    }

    return 0;
}

