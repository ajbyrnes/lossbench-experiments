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

# Iterate over mantissa bits and run benchmarks
for bits in {0..23}; do
    echo "Starting benchmark for bits $bits" | tee -a "$log_file"
    ./lossbench \
        --inputFile "$input_file" \
        --tree "$tree_name" \
        --branches "$branches" \
        --chunkSize "65536" \
        --compressor "zlib-trunc:compressionLevel=5,truncBits=$bits" \
        --resultsFile "$results_file" \
        --iterations 10 \
        >> "$log_file" 2>&1
    echo "Benchmark for bits $bits completed." | tee -a "$log_file"
done
