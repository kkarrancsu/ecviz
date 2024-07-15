import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import altair as alt

st.set_page_config(
    page_title="Eigenvector Centrality Visualization",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
)

rng = np.random.default_rng()
def get_weight():
    if weight_selection == "U[0,1)":
        return rng.uniform()
    elif weight_selection == "1":
        return 1

# graph initialization
def create_initial_clusters(n1, p1, n2, p2):
    seed = np.random.randint(1, 10000)
    G1 = nx.erdos_renyi_graph(n1, p1, seed=seed+1)
    G2 = nx.erdos_renyi_graph(n2, p2, seed=seed+2)

    # Assign random weights to edges
    for (u, v) in G1.edges():
        G1[u][v]['weight'] = get_weight()
    for (u, v) in G2.edges():
        G2[u][v]['weight'] = get_weight()

    G = nx.disjoint_union_all([G1, G2])
    return G, G1, G2

def update_weight(G, G1, G2, graph_id, u, v, new_weight):
    if graph_id == 1:
        if G1.has_edge(u, v):
            G1[u][v]['weight'] += new_weight
        else:
            G1.add_edge(u, v, weight=new_weight)
        # Update or create the edge in G
        if G.has_edge(u, v):
            G[u][v]['weight'] += new_weight
        else:
            G.add_edge(u, v, weight=new_weight)
    elif graph_id == 2:
        if G2.has_edge(u, v):
            G2[u][v]['weight'] += new_weight
        else:
            G2.add_edge(u, v, weight=new_weight)
        # Calculate the offset for nodes in G2
        offset = max(G1.nodes) + 1  # Assuming G1 nodes start from 0
        G_node_u = u + offset
        G_node_v = v + offset
        # Update or create the edge in G
        if G.has_edge(G_node_u, G_node_v):
            G[G_node_u][G_node_v]['weight'] += new_weight
        else:
            G.add_edge(G_node_u, G_node_v, weight=new_weight)

def calculate_eigenvector_centrality(G):
    ec_kwargs = {
        'max_iter': 1000,
        'tol': 1e-2,
    }
    if use_weight_compute_ec:
        ec_kwargs['weight'] = 'weight'
    centrality = nx.eigenvector_centrality(
        G, 
        **ec_kwargs
    )
    return centrality

def calculate_node_weight_sums(G):
    weight_sums = {node: 0 for node in G.nodes()}
    for u, v, data in G.edges(data=True):
        weight = data.get('weight', 1.0)
        weight_sums[u] += weight
        weight_sums[v] += weight
    return weight_sums

def plot_graph_and_heatmaps(G, step, pos, 
                            centrality_data_1, centrality_data_2, centrality_sums,
                            weight_sum_G1, weight_sum_G2, weight_sums):
    fig, ax1 = plt.subplots(figsize=(12,2))

    # Plot the graph
    centrality = calculate_eigenvector_centrality(G)
    node_color = [centrality[node] for node in G.nodes()]
    nx.draw(G, pos, ax=ax1, with_labels=True, node_size=500, node_color=node_color, cmap=plt.cm.Blues, font_size=10, font_color='black', font_weight='bold', edge_color='gray')
    ax1.set_title(f"Graph at Step {step}")
    
    st.pyplot(fig, use_container_width=True)
    
    centrality_df_1 = pd.DataFrame(centrality_data_1).reset_index().melt(id_vars='index').rename(columns={'index': 'Step', 'variable': 'Node', 'value': 'Centrality'})
    centrality_df_2 = pd.DataFrame(centrality_data_2).reset_index().melt(id_vars='index').rename(columns={'index': 'Step', 'variable': 'Node', 'value': 'Centrality'})

    # graph scaling
    vmin = min(centrality_df_1['Centrality'].min(), centrality_df_2['Centrality'].min())
    vmax = max(centrality_df_1['Centrality'].max(), centrality_df_2['Centrality'].max())
    heatmap_1 = alt.Chart(centrality_df_1).mark_rect().encode(
        x='Step:O',
        y='Node:O',
        color=alt.Color('Centrality:Q', scale=alt.Scale(scheme='blues', domain=[vmin, vmax]), legend=alt.Legend(title="Centrality")),
        tooltip=['Node', 'Step', 'Centrality']
    ).properties(
        title='Cluster 1 Eigenvector Centrality Heatmap'
    )
    heatmap_2 = alt.Chart(centrality_df_2).mark_rect().encode(
        x='Step:O',
        y='Node:O',
        color=alt.Color('Centrality:Q', scale=alt.Scale(scheme='blues', domain=[vmin, vmax]), legend=alt.Legend(title="Centrality")),
        tooltip=['Node', 'Step', 'Centrality']
    ).properties(
        title='Cluster 2 Eigenvector Centrality Heatmap'
    )

    centrality_sums_df = pd.DataFrame(centrality_sums, columns=['Step', 'Cluster 1', 'Cluster 2', 'Total'])
    centrality_sums_df = centrality_sums_df.melt(id_vars='Step', var_name='Cluster', value_name='Centrality Sum')
    line_plot = alt.Chart(centrality_sums_df).mark_line(point=True).encode(
        x='Step:O',
        y='Centrality Sum:Q',
        color='Cluster:N',
        tooltip=['Step', 'Cluster', 'Centrality Sum']
    ).properties(
        title='Sum of Eigenvector Centrality'
    )

    ## plotting weights
    weight_df_1 = pd.DataFrame(weight_sum_G1).reset_index().melt(id_vars='index').rename(columns={'index': 'Step', 'variable': 'Node', 'value': 'WeightSum'})
    weight_df_2 = pd.DataFrame(weight_sum_G2).reset_index().melt(id_vars='index').rename(columns={'index': 'Step', 'variable': 'Node', 'value': 'WeightSum'})

    # graph scaling
    vmin = min(weight_df_1['WeightSum'].min(), weight_df_2['WeightSum'].min())
    vmax = max(weight_df_1['WeightSum'].max(), weight_df_2['WeightSum'].max())
    heatmap_3 = alt.Chart(weight_df_1).mark_rect().encode(
        x='Step:O',
        y='Node:O',
        color=alt.Color('WeightSum:Q', scale=alt.Scale(scheme='greens', domain=[vmin, vmax]), legend=alt.Legend(title="WeightSum")),
        tooltip=['Node', 'Step', 'WeightSum']
    ).properties(
        title='Cluster 1 WeightSum Heatmap'
    )
    heatmap_4 = alt.Chart(weight_df_2).mark_rect().encode(
        x='Step:O',
        y='Node:O',
        color=alt.Color('WeightSum:Q', scale=alt.Scale(scheme='greens', domain=[vmin, vmax]), legend=alt.Legend(title="WeightSum")),
        tooltip=['Node', 'Step', 'WeightSum']
    ).properties(
        title='Cluster 2 WeightSum Heatmap'
    )

    weight_sums_df = pd.DataFrame(weight_sums, columns=['Step', 'Cluster 1', 'Cluster 2', 'Total'])
    weight_sums_df = weight_sums_df.melt(id_vars='Step', var_name='Cluster', value_name='Weight Sum')
    line_plot_sum = alt.Chart(weight_sums_df).mark_line(point=True).encode(
        x='Step:O',
        y='Weight Sum:Q',
        color='Cluster:N',
        tooltip=['Step', 'Cluster', 'Weight Sum']
    ).properties(
        title='Sum of Weights'
    )

    st.altair_chart(
        alt.vconcat(
            alt.hconcat(
                heatmap_1.properties(width=200, height=200),
                heatmap_2.properties(width=200, height=200),
                line_plot.properties(width=300, height=200)
            ),
            alt.hconcat(
                heatmap_3.properties(width=200, height=200),
                heatmap_4.properties(width=200, height=200),
                line_plot_sum.properties(width=300, height=200)
            ),
        ),
        # use_container_width=True
    )

# st.sidebar.title("Graph Configuration")
n1 = st.sidebar.slider("Number of nodes in Cluster 1", 1, 20, 5)
p1 = st.sidebar.slider("Probability of edge creation in Cluster 1", 0.1, 1.0, 0.25)
n2 = st.sidebar.slider("Number of nodes in Cluster 2", 1, 20, 15)
p2 = st.sidebar.slider("Probability of edge creation in Cluster 2", 0.1, 1.0, 0.75)
weight_selection = st.sidebar.radio("Weight Selection", ["U[0,1)", "1"])
ec_compute_selection = st.sidebar.radio("EC Compute Cluster Setting", ["Separate", "Together"])
use_weight_compute_ec = st.sidebar.radio("Use Weight to Compute Eigenvector Centrality", ["Yes", "No"])
initiate = st.sidebar.button("Reset/Start")

if initiate:
    # Step 1: Create the initial clusters
    G, G1, G2 = create_initial_clusters(n1, p1, n2, p2)

    # Initial positions for the graph layout
    pos = nx.spring_layout(G)

    # Initialize the step tracker
    st.session_state.step = 0
    st.session_state['G'] = G
    st.session_state['G1'] = G1
    st.session_state['G2'] = G2
    st.session_state['pos'] = pos
    st.session_state['centrality_sums'] = []
    st.session_state['centrality_data_cluster1'] = []
    st.session_state['centrality_data_cluster2'] = []
    st.session_state['weight_sum_G1'] = []
    st.session_state['weight_sum_G2'] = []
    st.session_state['weight_sums'] = []

    # Centrality Computation
    if ec_compute_selection == "Together":
        centrality = calculate_eigenvector_centrality(G)
        centrality_data_1 = [centrality[node] for node in range(G1.number_of_nodes())]
        centrality_data_2 = [centrality[node] for node in range(G1.number_of_nodes(), G1.number_of_nodes() + G2.number_of_nodes())]
        centrality_sum_1 = sum(centrality[node] for node in range(G1.number_of_nodes()))
        centrality_sum_2 = sum(centrality[node] for node in range(G1.number_of_nodes(), G1.number_of_nodes() + G2.number_of_nodes()))
        total_centrality_sum = sum(centrality.values())
    elif ec_compute_selection == "Separate":
        c1 = calculate_eigenvector_centrality(G1)
        c2 = calculate_eigenvector_centrality(G2)
        centrality_data_1 = [c1[node] for node in range(G1.number_of_nodes())]
        centrality_data_2 = [c2[node] for node in range(G2.number_of_nodes())]
        centrality_sum_1 = sum(c1.values())
        centrality_sum_2 = sum(c2.values())
        total_centrality_sum = centrality_sum_1 + centrality_sum_2
    
    # Weight Computation
    weights_G1 = calculate_node_weight_sums(G1)
    weights_G2 = calculate_node_weight_sums(G2)
    weight_sum_1 = sum(weights_G1.values())
    weight_sum_2 = sum(weights_G2.values())
    total_weight_sum = weight_sum_1 + weight_sum_2
    
    # the first element in this array is the "step" of the simulation
    st.session_state['centrality_sums'].append([0, centrality_sum_1, centrality_sum_2, total_centrality_sum])
    st.session_state['centrality_data_cluster1'].append(centrality_data_1)
    st.session_state['centrality_data_cluster2'].append(centrality_data_2)
    st.session_state['weight_sum_G1'].append(weights_G1)
    st.session_state['weight_sum_G2'].append(weights_G2)
    st.session_state['weight_sums'].append([0, weight_sum_1, weight_sum_2, total_weight_sum])


# Check if the step tracker is initialized
if 'step' in st.session_state:
    G = st.session_state.G
    G1 = st.session_state.G1
    G2 = st.session_state.G2
    pos = st.session_state.pos

    if st.sidebar.button("Next"):
        st.session_state.step += 1

    # randomly select two nodes that transact in each cluster, and update the weights accordingly
    for i in range(2):
        u = np.random.randint(0, G1.number_of_nodes())
        v = np.random.randint(0, G1.number_of_nodes())
        new_weight = get_weight()
        update_weight(G, G1, G2, 1, u, v, new_weight)
        
        u = np.random.randint(0, G2.number_of_nodes())
        v = np.random.randint(0, G2.number_of_nodes())
        new_weight = get_weight()
        update_weight(G, G1, G2, 2, u, v, new_weight)

    # Calculate eigenvector centrality for the current graph
    if ec_compute_selection == "Together":
        centrality = calculate_eigenvector_centrality(G)
        centrality_data_1 = [centrality[node] for node in range(G1.number_of_nodes())]
        centrality_data_2 = [centrality[node] for node in range(G1.number_of_nodes(), G1.number_of_nodes() + G2.number_of_nodes())]
        centrality_sum_1 = sum(centrality[node] for node in range(G1.number_of_nodes()))
        centrality_sum_2 = sum(centrality[node] for node in range(G1.number_of_nodes(), G1.number_of_nodes() + G2.number_of_nodes()))
        total_centrality_sum = sum(centrality.values())
    elif ec_compute_selection == "Separate":
        c1 = calculate_eigenvector_centrality(G1)
        c2 = calculate_eigenvector_centrality(G2)
        centrality_data_1 = [c1[node] for node in range(G1.number_of_nodes())]
        centrality_data_2 = [c2[node] for node in range(G2.number_of_nodes())]
        centrality_sum_1 = sum(c1.values())
        centrality_sum_2 = sum(c2.values())
        total_centrality_sum = centrality_sum_1 + centrality_sum_2

    st.session_state['centrality_data_cluster1'].append(centrality_data_1)
    st.session_state['centrality_data_cluster2'].append(centrality_data_2)
    st.session_state['centrality_sums'].append([st.session_state.step, centrality_sum_1, centrality_sum_2, total_centrality_sum])

    weight_G1 = calculate_node_weight_sums(G1)
    weight_G2 = calculate_node_weight_sums(G2)
    weight_sum_1 = sum(weight_G1.values())
    weight_sum_2 = sum(weight_G2.values())
    total_weight_sum = weight_sum_1 + weight_sum_2
    st.session_state['weight_sum_G1'].append(weight_G1)
    st.session_state['weight_sum_G2'].append(weight_G2)
    st.session_state['weight_sums'].append([st.session_state.step, weight_sum_1, weight_sum_2, total_weight_sum])

    # Plot the graph and heatmaps
    plot_graph_and_heatmaps(
        G, 
        st.session_state.step, 
        pos, 
        st.session_state['centrality_data_cluster1'], 
        st.session_state['centrality_data_cluster2'], 
        st.session_state['centrality_sums'],
        st.session_state['weight_sum_G1'], 
        st.session_state['weight_sum_G2'], 
        st.session_state['weight_sums'],
    )

    st.session_state['G'] = G