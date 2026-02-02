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
tree_name="mini"
branches="lep_pt,lep_eta,lep_phi,lep_E"
# tree_name="CollectionTree"
# branches="AnalysisJetsAuxDyn.pt,AnalysisJetsAuxDyn.eta,AnalysisJetsAuxDyn.phi"
chunk_sizes=(1024 2048 4096 8192 16384 32768 65536 131072 262144 524288 1048576)
rel_error_bounds=(0.0001)

# Iterate over algorithms
# 0 = ALGO_LORENZO_REG
# 1 = ALGO_INTERP_LORENZO
# 2 = ALGO_INTERP
# 3 = ALGO_NOPRED
for algo in {0..3}; do
    for chunk_size in "${chunk_sizes[@]}"; do
        for rel_error_bound in "${rel_error_bounds[@]}"; do
            decompFile="$results_dir/sz3_${algo}_chunk${chunk_size}_eb${rel_error_bound}.root"

            echo "Starting benchmark for algorithm $algo with chunk size $chunk_size" | tee -a "$log_file"
            ./lossbench \
                --inputFile "$input_file" \
                --tree "$tree_name" \
                --branches "$branches" \
                --chunkSize "$chunk_size" \
                --compressor "sz3:cmprAlgo=$algo,errorBoundMode=1,relErrorBound=$rel_error_bound" \
                --resultsFile "$results_file" \
                --decompFile "$decompFile" \
                # --iterations 10 \
                >> "$log_file" 2>&1
            echo "Benchmark for algorithm $algo with chunk size $chunk_size completed." | tee -a "$log_file"
        done
    done
    echo "Benchmark for algorithm $algo completed." | tee -a "$log_file"
done
