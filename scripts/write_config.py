#!/usr/bin/env python3
"""
Generate lossbench config files.
Uncomment the desired generators in main().
"""

import json

INPUT_FILE = "DAOD_PHYSLITE.37019878._000009.pool.root.1"
TREE_NAME = "CollectionTree"

CHUNK_SIZES = [16384, 32768, 65536, 131072, 262144, 524288, 1048576, 2097152, 4194304, 8388608, 16777216]
ERROR_BOUNDS = [100, 10, 1, 1e-1, 1e-2, 1e-3, 1e-4, 1e-5, 1e-6]
BITRATES = [2, 4, 8, 10, 12, 16, 20, 24, 26, 28, 30, 32]
MANTISSA_BITS = [2, 4, 8, 10, 12, 14, 16, 18, 20, 22]
ITERATIONS = 5

ALL_BRANCHES = [
    "AnalysisSiHitElectronsAuxDyn.pt", "AnalysisSiHitElectronsAuxDyn.eta", "AnalysisSiHitElectronsAuxDyn.phi",
    "AnalysisJetsAuxDyn.pt", "AnalysisJetsAuxDyn.eta", "AnalysisJetsAuxDyn.phi"
]


def write_config(config, filename):
    with open(filename, "w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")
    print(f"Wrote {len(config['tests'])} tests to {filename}")


def make_config(branches, tests):
    return {
        "inputFile": INPUT_FILE,
        "tree":      TREE_NAME,
        "branches":  branches,
        "tests":     tests,
    }
   

def trunc_sweep():
    tests = [
        {
            "compressor": "zstd-trunc",
            "options": {
                "compressionLevel": "5",
                "truncBits": str(tb)
            },
            "normalize": False,
            "chunkSize": c, "iterations": ITERATIONS
        }
        for tb in MANTISSA_BITS for c in CHUNK_SIZES
    ]
    
    write_config(
        make_config(ALL_BRANCHES, tests),
        "zstd-trunc-sweep-config.json"
    )
    
    
SZ3_ALGOS = [0, 1, 2, 3]  # 0=LORENZO_REG, 1=INTERP_LORENZO, 2=INTERP, 3=NOPRED

def sz3_sweep():
    abs_err_tests = [
        {
            "compressor": "sz3",
            "options": {
                "cmprAlgo": str(a), 
                "errorBoundMode": "0",
                "absErrorBound": str(eb)
            },
            "normalize": False,
            "chunkSize": c, "iterations": ITERATIONS}
        for a in SZ3_ALGOS for eb in ERROR_BOUNDS for c in CHUNK_SIZES
    ]
    
    rel_err_tests = [
        {
            "compressor": "sz3",
            "options": {
                "cmprAlgo": str(a), 
                "errorBoundMode": "1",
                "relErrorBound": str(eb)
            },
            "normalize": False,
            "chunkSize": c, "iterations": ITERATIONS}
        for a in SZ3_ALGOS for eb in ERROR_BOUNDS for c in CHUNK_SIZES
    ]

    write_config(
        make_config(ALL_BRANCHES, abs_err_tests + rel_err_tests),
        "sz3-sweep-config.json"
    )


def sperr_sweep():
    bitrate_tests = [
        {
            "compressor": "sperr",
            "options": {"bitrate": str(br)},
            "normalize": False,
            "chunkSize": c,
            "iterations": ITERATIONS
        }
        for br in BITRATES for c in CHUNK_SIZES
    ]
    
    pwe_tests = [
        {
            "compressor": "sperr",
            "options": {"pwe": str(pwe)},
            "normalize": False,
            "chunkSize": c,
            "iterations": ITERATIONS
        }
        for pwe in ERROR_BOUNDS for c in CHUNK_SIZES
    ]
    
    write_config(
        make_config(ALL_BRANCHES, bitrate_tests + pwe_tests), 
        "sperr-sweep-config.json"
    )
    
MGARD_SMOOTHNESS = [-1, 0, 1]    

def mgard_sweep():
    tests = [
        {
            "compressor": "mgard",
            "options": {
                "tolerance": str(eb),
                "smoothness": str(s)
            },
            "normalize": False,
            "chunkSize": c,
            "iterations": ITERATIONS
        }
        for s in MGARD_SMOOTHNESS for eb in ERROR_BOUNDS for c in CHUNK_SIZES
    ]
    
    write_config(
        make_config(ALL_BRANCHES, tests), 
        "mgard-sweep-config.json"
    )
    
def zfpx_sweep():
    abs_eb_tests = [
        {
            "compressor": "zfpx",
            "options": {
                "mode": "accuracy",
                "tolerance": str(eb)
            },
            "normalize": False,
            "chunkSize": c,
            "iterations": ITERATIONS
        }
        for eb in ERROR_BOUNDS for c in CHUNK_SIZES
    ]
    
    bitrate_tests = [
        {
            "compressor": "zfpx",
            "options": {
                "mode": "rate",
                "rate": str(br)
            },
            "normalize": False,
            "chunkSize": c,
            "iterations": ITERATIONS
        }
        for br in BITRATES for c in CHUNK_SIZES
    ]
    
    trunc_tests = [
        {
            "compressor": "zfpx",
            "options": {
                "mode": "precision",
                "precision": str(tb)
            },
            "normalize": False,
            "chunkSize": c,
            "iterations": ITERATIONS
        }
        for tb in MANTISSA_BITS for c in CHUNK_SIZES
    ]
    
    write_config(
        make_config(ALL_BRANCHES, abs_eb_tests + bitrate_tests + trunc_tests),
        "zfpx-sweep-config.json"
    )
    
def main():
    trunc_sweep()
    sz3_sweep()
    sperr_sweep()
    mgard_sweep()
    zfpx_sweep()

if __name__ == "__main__":
    main()