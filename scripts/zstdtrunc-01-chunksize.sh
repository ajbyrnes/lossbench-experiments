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
chunk_sizes=(1024 2048 4096 8192 16384 32768 65536 131072 262144 524288 1048576)

# Iterate over chunk sizes and run benchmarks
for chunk_size in "${chunk_sizes[@]}"; do
    echo "Starting benchmark for chunk size $chunk_size" | tee -a "$log_file"
    ./lossbench \
        --inputFile "$input_file" \
        --tree "$tree_name" \
        --branches "$branches" \
        --chunkSize "$chunk_size" \
        --compressor "zstd-trunc:compressionLevel=5,truncBits=8" \
        --resultsFile "$results_file" \
        --iterations 10 \
        >> "$log_file" 2>&1
    echo "Benchmark for chunk size $chunk_size completed." | tee -a "$log_file"
done
