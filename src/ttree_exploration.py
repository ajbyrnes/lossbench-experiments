import uproot
import pandas as pd

from plotly import graph_objects as go
import math

def list_trees(filepath):
    """List all trees in a ROOT file."""
    with uproot.open(filepath) as file:
        trees = {name: obj for name, obj in file.items() if isinstance(obj, uproot.TTree)}
        return trees


def categorize_dtype(interpretation):
    """Classify a branch's interpretation into a human-readable type category."""
    interp_str = str(interpretation)
    
    # Normalize endianness markers - both >f4 and <f4 are just float32
    # > = big-endian, < = little-endian (ROOT uses big-endian historically)
    normalized = interp_str.replace('>f4', 'float32').replace('<f4', 'float32')
    normalized = normalized.replace('>f8', 'float64').replace('<f8', 'float64')
    normalized = normalized.replace('>i4', 'int32').replace('<i4', 'int32')
    normalized = normalized.replace('>i8', 'int64').replace('<i8', 'int64')
    normalized = normalized.replace('>u4', 'uint32').replace('<u4', 'uint32')
    normalized = normalized.replace('>u8', 'uint64').replace('<u8', 'uint64')
    interp_str = normalized
    
    # Check for jagged/variable-length arrays (std::vector equivalents)
    if 'var *' in interp_str or 'Jagged' in interp_str:
        if 'float32' in interp_str:
            return 'vector<float>'
        elif 'float64' in interp_str or 'double' in interp_str:
            return 'vector<double>'
        elif 'int32' in interp_str:
            return 'vector<int32>'
        elif 'int64' in interp_str:
            return 'vector<int64>'
        elif 'uint32' in interp_str:
            return 'vector<uint32>'
        elif 'uint8' in interp_str or 'bool' in interp_str.lower():
            return 'vector<uint8/bool>'
        else:
            return f'vector<other>'
    # Fixed-size arrays
    elif '[' in interp_str and ']' in interp_str:
        if 'float32' in interp_str:
            return 'array<float>'
        elif 'float64' in interp_str:
            return 'array<double>'
        else:
            return f'array<other>'
    # Scalars
    elif 'float32' in interp_str:
        return 'float'
    elif 'float64' in interp_str:
        return 'double'
    elif 'int32' in interp_str:
        return 'int32'
    elif 'int64' in interp_str:
        return 'int64'
    elif 'uint32' in interp_str:
        return 'uint32'
    elif 'bool' in interp_str.lower() or 'uint8' in interp_str:
        return 'uint8/bool'
    else:
        return f'other'
    
    
def get_branch_info(tree):
    branches = []
    for branch_name, branch in tree.items():
        try:
            # Append a record for each branch
            dtype_category = categorize_dtype(branch.interpretation)
            compressed_bytes = branch.compressed_bytes
            uncompressed_bytes = branch.uncompressed_bytes
            
            if uncompressed_bytes > 0:
                compression_ratio = uncompressed_bytes / compressed_bytes if compressed_bytes > 0 else float('inf')
            else:
                compression_ratio = 1.0
                
            branches.append({
                'branch': branch_name,
                'container': branch_name.split('.')[0] if '.' in branch_name else branch_name,
                'dtype_category': dtype_category,
                'interpretation': str(branch.interpretation),
                'compressed_bytes': compressed_bytes,
                'uncompressed_bytes': uncompressed_bytes,
                'compression_ratio': compression_ratio,
            })
        except Exception as e:
            print(f"Branch: {branch_name}, Error determining type: {e}")
            
    return pd.DataFrame(branches)


def analyze_file(filepath):
    """Analyze a ROOT file and return branch-level compression statistics."""
    
    print(f"Opening: {filepath}\n")    
    f = uproot.open(filepath)

    trees = {k: v for k, v in f.items() if isinstance(v, uproot.TTree)}
    if not trees:
        print("No TTrees found in file!")
        return None
    
    all_branches = []
    for tree_name, tree in trees.items():
        print(f"Tree: {tree_name}")
        print(f"  Entries: {tree.num_entries:,}")
        print()
        
        for branch_name, branch in tree.items():
            try:
                interp = branch.interpretation
                dtype_category = categorize_dtype(str(interp))
                
                # Get compression info
                compressed_bytes = branch.compressed_bytes
                uncompressed_bytes = branch.uncompressed_bytes
                
                if uncompressed_bytes > 0:
                    ratio = uncompressed_bytes / compressed_bytes if compressed_bytes > 0 else float('inf')
                else:
                    ratio = 1.0
                
                all_branches.append({
                    'tree': tree_name,
                    'branch': branch_name,
                    'dtype_category': dtype_category,
                    'interpretation': str(interp),
                    'compressed_bytes': compressed_bytes,
                    'uncompressed_bytes': uncompressed_bytes,
                    'compression_ratio': ratio,
                })
            except Exception as e:
                print(f"  Warning: Could not process branch {branch_name}: {e}")
    
    return pd.DataFrame(all_branches)


def summarize_by_dtype(df):
    """Summarize compression statistics grouped by data type category."""

    summary = df.groupby('dtype_category').agg({
        'compressed_bytes': 'sum',
        'uncompressed_bytes': 'sum',
        'branch': 'count',
    }).rename(columns={'branch': 'num_branches'})
    
    summary['compression_ratio'] = summary['uncompressed_bytes'] / summary['compressed_bytes']
    summary['pct_of_compressed'] = 100 * summary['compressed_bytes'] / summary['compressed_bytes'].sum()
    summary['pct_of_uncompressed'] = 100 * summary['uncompressed_bytes'] / summary['uncompressed_bytes'].sum()
    
    summary['compressed_mb'] = summary['compressed_bytes'] / 1e6
    summary['uncompressed_mb'] = summary['uncompressed_bytes'] / 1e6
    summary['reduction_pct'] = 100 * (1 - summary['compressed_bytes'] / summary['uncompressed_bytes'])
    
    # Sort by compressed size descending
    summary = summary.sort_values('compressed_bytes', ascending=False)
    
    return summary


def print_summary(summary):
    """Print a formatted summary of the analysis."""
    
    total_compressed = summary['compressed_bytes'].sum()
    total_uncompressed = summary['uncompressed_bytes'].sum()
    overall_ratio = total_uncompressed / total_compressed if total_compressed > 0 else 1.0
    
    print("=" * 80)
    print("OVERALL FILE SUMMARY")
    print("=" * 80)
    print(f"Total branches:       {summary['num_branches'].sum():,}")
    print(f"Compressed size:      {total_compressed / 1e6:.2f} MB")
    print(f"Uncompressed size:    {total_uncompressed / 1e6:.2f} MB")
    print(f"Overall compression:  {overall_ratio:.2f}x")
    print()
    
    print("=" * 80)
    print("SUMMARY BY DATA TYPE")
    print("=" * 80)
    print()
    
    # Format for display
    for dtype_cat in summary.index:
        row = summary.loc[dtype_cat]
        print(f"{dtype_cat}")
        print(f"  Branches:          {int(row['num_branches']):,}")
        print(f"  Compressed:        {row['compressed_bytes'] / 1e6:.2f} MB ({row['pct_of_compressed']:.1f}% of file)")
        print(f"  Uncompressed:      {row['uncompressed_bytes'] / 1e6:.2f} MB ({row['pct_of_uncompressed']:.1f}%)")
        print(f"  Compression ratio: {row['compression_ratio']:.2f}x")
        print()
    
    # Highlight vector<float> specifically
    print("=" * 80)
    print("VECTOR<FLOAT> FOCUS")
    print("=" * 80)
    
    if 'vector<float>' in summary.index:
        vf = summary.loc['vector<float>']
        print(f"vector<float> is {vf['pct_of_compressed']:.1f}% of compressed file size")
        print(f"vector<float> is {vf['pct_of_uncompressed']:.1f}% of uncompressed file size")
        print(f"vector<float> compresses at {vf['compression_ratio']:.2f}x")
        
        # Compare to other types
        other_vectors = summary[summary.index.str.startswith('vector<') & (summary.index != 'vector<float>')]
        if len(other_vectors) > 0:
            other_ratio = other_vectors['uncompressed_bytes'].sum() / other_vectors['compressed_bytes'].sum()
            print(f"Other vector types compress at {other_ratio:.2f}x")
        
        scalars = summary[~summary.index.str.startswith('vector<') & ~summary.index.str.startswith('array<')]
        if len(scalars) > 0:
            scalar_ratio = scalars['uncompressed_bytes'].sum() / scalars['compressed_bytes'].sum()
            print(f"Scalar types compress at {scalar_ratio:.2f}x")
    else:
        print("No vector<float> branches found in this file.")
    
    print()
    
    
def print_top_branches(df, n=20):
    """Print the top N branches by compressed size."""
    
    print("=" * 80)
    print(f"TOP {n} BRANCHES BY COMPRESSED SIZE")
    print("=" * 80)
    print()
    
    top = df.nlargest(n, 'compressed_bytes')
    
    for _, row in top.iterrows():
        print(f"{row['branch']}: {row['dtype_category']}, ")
        print(f"  Type:        {row['dtype_category']}")
        print(f"  Compressed:  {row['compressed_bytes'] / 1e6:.3f} MB")
        print(f"  Ratio:       {row['compression_ratio']:.2f}x")
        print()
        
def plot_reduction_by_dtype(summary, filepath):
    fig = go.Figure()

    # Uncompressed bars (background)
    fig.add_trace(go.Bar(
        y=summary.index,
        x=summary['uncompressed_mb'],
        name='Uncompressed',
        orientation='h',
        marker_color='lightgray',
        text=[f"{x:.0f} MB" for x in summary['uncompressed_mb']],
        textposition='inside',
    ))

    # Compressed bars (foreground)
    fig.add_trace(go.Bar(
        y=summary.index,
        x=summary['compressed_mb'],
        name='Compressed',
        orientation='h',
        marker_color='steelblue',
        text=[f"{x:.0f} MB" for x in summary['compressed_mb']],
        textposition='inside',
    ))

    for i, (dtype, row) in enumerate(summary.iterrows()):
        fig.add_annotation(
            x=math.log10(row['uncompressed_mb']),
            y=dtype,
            text=f"-{row['reduction_pct']:.0f}%",
            showarrow=False,
            xanchor='left',
            xshift=10,
            font=dict(size=11, color='red'),
        )

    fig.update_layout(
        title='Reduction in Size by Data Type',
        title_subtitle_text=f"{filepath.split('/')[-1]}",
        xaxis_title='Size (MB)',
        xaxis_type='log',
        yaxis_title='Data Type',
        barmode='overlay',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        height=500,
        width=900,
        margin=dict(l=120, r=100, t=80, b=60),
    )
    
    return fig


def plot_reduction_by_branch(df, filepath, reduction_pct, n=10):
    # Get top N branches by compressed size within vector<float>
    df_copy = df.copy()
    df_copy['reduction_pct'] = 100 * (1 - df_copy['compressed_bytes'] / df_copy['uncompressed_bytes'])
    vector_float_branches = df_copy[df_copy['dtype_category'] == 'vector<float>']
    filtered = vector_float_branches[vector_float_branches['reduction_pct'] < reduction_pct]
    top_branches = filtered.nsmallest(n, 'compressed_bytes')
    
    # Sort by branch name
    top_branches = top_branches.sort_values('branch', ascending=True)

    fig = go.Figure()
    
    # Uncompressed bars (background)
    fig.add_trace(go.Bar(
        y=top_branches['branch'],
        x=top_branches['uncompressed_bytes'] / 1e6,
        name='Uncompressed',
        orientation='h',
        marker_color='lightgray',
        text=[f"{x:.0f} MB" for x in top_branches['uncompressed_bytes'] / 1e6],
        textposition='inside',
    ))
    
    # Compressed bars (foreground)
    fig.add_trace(go.Bar(
        y=top_branches['branch'],
        x=top_branches['compressed_bytes'] / 1e6,
        name='Compressed',
        orientation='h',
        marker_color='steelblue',
        text=[f"{x:.0f} MB" for x in top_branches['compressed_bytes'] / 1e6],
        textposition='inside',
    ))
    
    for i, (idx, row) in enumerate(top_branches.iterrows()):
        fig.add_annotation(
            x=row['uncompressed_bytes'] / 1e6,
            y=row['branch'],
            text=f"-{row['reduction_pct']:.0f}%",
            showarrow=False,
            xanchor='left',
            xshift=10,
            font=dict(size=11, color='red'),
        )
        
        
    fig.update_layout(
        title=f'vector<float> branches with <= {reduction_pct}% reduction',
        title_subtitle_text=f"{filepath.split('/')[-1]}",
        xaxis_title='Size (MB)',
        # xaxis_type='log',
        yaxis_title='Branch',
        barmode='overlay',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        height=(n * 35 + 150),
        width=900,
        margin=dict(l=120, r=100, t=80, b=60),
    )
    
    return fig