import uproot
import awkward as ak
import pandas as pd
import numpy as np

from plotly import graph_objects as go
import math

from src.ttree_exploration import list_trees, get_branch_info

def create_branch_df(filepath, outfile='branch_data.csv', tree='CollectionTree;1', filters=None):
    # Load branch metadata
    collection_tree_df = get_branch_info(list_trees(filepath).get(tree))
    
    # Add file name to dataframe
    collection_tree_df['file'] = filepath.split('/')[-1]
    
    # Filter for vector<float> branches
    vector_float_df = collection_tree_df[collection_tree_df['dtype_category'] == 'vector<float>']
    
    # Apply additional filters if provided
    if filters is not None:
        for filter in filters:
            vector_float_df = vector_float_df[~vector_float_df['branch'].str.contains(filter, na=False)]
    
    # Create empty stats columns
    vector_float_df['mean'] = None
    vector_float_df['std'] = None
    vector_float_df['min'] = None
    vector_float_df['max'] = None
    vector_float_df['dynamic_range'] = None
    
    # Load data and compute statistics
    with uproot.open(filepath) as file:
        tree = file[tree]
        for index, row in vector_float_df.iterrows():
            branch_data = tree[row['branch']].array(library='ak')
            flat_data = ak.flatten(branch_data)
            if len(flat_data) > 0:
                mean = ak.mean(flat_data)
                std = ak.std(flat_data)
                min_val = ak.min(flat_data)
                max_val = ak.max(flat_data)
                dynamic_range = max_val - min_val
                
                vector_float_df.at[index, 'mean'] = mean
                vector_float_df.at[index, 'std'] = std
                vector_float_df.at[index, 'min'] = min_val
                vector_float_df.at[index, 'max'] = max_val
                vector_float_df.at[index, 'dynamic_range'] = dynamic_range
    
    vector_float_df.to_csv(outfile, index=False)
    print(f'Branch statistics saved to {outfile}') 


def load_branch_data(filepath, branch, tree='CollectionTree;1'):
    with uproot.open(filepath) as file:
        tree = file[tree]
        branch_data = tree[branch].array(library='ak')
    return branch_data
    
    
def plot_branch_histogram(branch_data, branch_name, color, bins=100):
    hist_data = ak.flatten(branch_data)
    counts, bin_edges = np.histogram(hist_data, bins=bins)
    bin_centers = 0.5 * (bin_edges[1:] + bin_edges[:-1])

    fig = go.Figure(data=go.Bar(x=bin_centers, y=counts, marker_color=color))
    
    fig.update_layout(
        title=f"{branch_name} Distribution",
        xaxis_title=branch_name,
        yaxis_title="Counts",
        bargap=0,
        height=400,
        width=600
    )
    
    return fig