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
# tree_name="mini"
# branches="lep_pt,lep_eta,lep_phi,lep_E"
tree_name="CollectionTree"
branches="AnalysisJetsAuxDyn.pt,AnalysisJetsAuxDyn.eta,AnalysisJetsAuxDyn.phi"
chunk_sizes=(131072 262144 524288 1048576)
precisions=(5 2 1 0.5 0.2 0.1 0.05 0.01)

# Iterate over precision values
for precision in "${precisions[@]}"; do
    for chunk_size in "${chunk_sizes[@]}"; do
        decompFile="$results_dir/mgard.${timestamp}.root"

        echo "Starting benchmark for MGARD precision $precision with chunk size $chunk_size" | tee -a "$log_file"
        ./lossbench \
            --inputFile "$input_file" \
            --tree "$tree_name" \
            --branches "$branches" \
            --chunkSize "$chunk_size" \
            --compressor "mgard:mode=abs,tolerance=$precision" \
            --resultsFile "$results_file" \
            # --decompFile "$decompFile" \
            # --iterations 10 \
            >> "$log_file" 2>&1
        echo "Benchmark for MGARD precision $precision with chunk size $chunk_size completed." | tee -a "$log_file"
    done
    echo "Benchmark for MGARD precision $precision completed." | tee -a "$log_file"
done