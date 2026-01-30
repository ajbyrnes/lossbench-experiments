#!/bin/bash

# Results directory and file setup
script_name=$(basename "$0")
timestamp=$(date +"%Y%m%d_%H%M%S")

results_dir="${script_name}.${timestamp}"
mkdir -p "$results_dir"

results_file="$results_dir/results.jsonl"
log_file="$results_dir/benchmark.log"

# Benchmark parameters
input_file="data.root"
tree_name="CollectionTree"
branches="AnalysisJetsAuxDyn.pt,AnalysisJetsAuxDyn.eta,AnalysisJetsAuxDyn.phi,AnalysisElectronsAuxDyn.pt,AnalysisElectronsAuxDyn.eta,AnalysisElectronsAuxDyn.phi"
# chunk_sizes=(1024 2048 4096 8192 16384 32768 65536 131072 262144 524288 1048576)
rel_error_bounds=(0.01 0.001 0.0001 0.00001 0.000001)

# Iterate over algorithms
# 0 = ALGO_LORENZO_REG
# 1 = ALGO_INTERP_LORENZO
# 2 = ALGO_INTERP
# 3 = ALGO_NOPRED
for algo in {0..3}; do
    for rel_error in "${rel_error_bounds[@]}"; do
        echo "Starting benchmark for algorithm $algo with relative error bound $rel_error" | tee -a "$log_file"
        ./lossbench \
            --inputFile "$input_file" \
            --tree "$tree_name" \
            --branches "$branches" \
            --chunkSize "65536" \
            --compressor "sz3:cmprAlgo=$algo,errorBoundMode=1,relErrorBound=$rel_error" \
            --resultsFile "$results_file" \
            --iterations 10 \
            >> "$log_file" 2>&1
        echo "Benchmark for algorithm $algo with relative error bound $rel_error completed." | tee -a "$log_file"
    done
    echo "Benchmark for algorithm $algo completed." | tee -a "$log_file"
done
