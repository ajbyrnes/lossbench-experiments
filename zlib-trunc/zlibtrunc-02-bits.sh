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

# Iterate over mantissa bits and run benchmarks
for bits in 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23; do
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
