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
branches="AnalysisJetsAuxDyn.pt,AnalysisJetsAuxDyn.eta,AnalysisJetsAuxDyn.phi"
chunk_sizes=(16384 32768 65536 131072 262144 524288 1048576)
error_rates=(0.1 0.01 0.001)
transforms=("bsplines" "wavelets")

# Iterate over transforms and error rates
for transform in "${transforms[@]}"; do
    for error_rate in "${error_rates[@]}"; do
        for chunk_size in "${chunk_sizes[@]}"; do
            echo "Starting benchmark for ISABELA transform=$transform errorRate=$error_rate chunkSize=$chunk_size" | tee -a "$log_file"
            ./lossbench \
                --inputFile "$input_file" \
                --tree "$tree_name" \
                --branches "$branches" \
                --chunkSize "$chunk_size" \
                --compressor "isabela:transform=$transform,errorRate=$error_rate" \
                --resultsFile "$results_file" \
                >> "$log_file" 2>&1
            echo "Benchmark for ISABELA transform=$transform errorRate=$error_rate chunkSize=$chunk_size completed." | tee -a "$log_file"
        done
        echo "Benchmark for ISABELA transform=$transform errorRate=$error_rate completed." | tee -a "$log_file"
    done
done
