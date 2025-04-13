import tkinter as tk
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.patches as mpatches

# Build course graph
# df: dataframe containing prerequisites
def get_graph(df):
	course_graph = nx.DiGraph()

	# Add courses as nodes
	for _, row in df.iterrows():
		course_name = f"{row['Department']}{row['Course Number']}"
		course_graph.add_node(course_name)

	# Add edges
	for _, row in df.iterrows():
		if row["Parsed Prerequisites"] != "N/A":
			course_name = f"{row['Department']}{row['Course Number']}"
			prerequisites = row["Parsed Prerequisites"].split(", ")
			for prereq in prerequisites:
				prereq = prereq.strip()
				if prereq:
					course_graph.add_edge(prereq, course_name)
     
	return course_graph

# Custom graph layout based on depth
def custom_layout(graph, selected_course, prerequisites):
    pos = {}
    pos[selected_course] = (0, 0)
    
    # Place prerequisites on the left (x < 0), centered around 0
    for i, prereq in enumerate(prerequisites):
        y_offset = (i - (len(prerequisites) - 1)/2)
        pos[prereq] = (-1, y_offset)
    
    # Calculate node depths (BFS)
    depths = {selected_course: 0}
    queue = [selected_course]
    while queue:
        current = queue.pop(0)
        for neighbor in graph.successors(current):
            if neighbor not in depths and neighbor != selected_course:
                depths[neighbor] = depths[current] + 1
                queue.append(neighbor)
    
    depth_counters = {}
    global_x_offset = 0
    
    # Place nodes by depth, alternating above/below the center
    for node, depth in depths.items():
        if node != selected_course and node not in prerequisites:
            if depth not in depth_counters:
                depth_counters[depth] = 0
            
            if depth_counters[depth] > 0 and depth_counters[depth] % 7 == 0:
                global_x_offset += 1
            
            # Calculate adjusted x position (increment if >7 nodes at this depth to make it more)
            x_pos = depth + global_x_offset
            # Calculate y, alternate above and below the center
            y_pos = (depth_counters[depth] % 7 + 1) // 2 * (1 if (depth_counters[depth] % 7) % 2 == 0 else -1)
            
            pos[node] = (x_pos, y_pos)
            
            depth_counters[depth] += 1
    
    return pos

def create_filtered_graph(course_graph, selected_course):
    """Create a filtered subgraph based on the selected course."""
    # Filtering logic
    prerequisites = list(course_graph.predecessors(selected_course))
    direct_neighbors = list(course_graph.neighbors(selected_course))
    filtered_subgraph = nx.DiGraph()

    if len(direct_neighbors) < 8:
        # Case 1: Fewer than 5 direct neighbors, show prerequisites + all unlocks
        unlocks = list(nx.descendants(course_graph, selected_course))
        nodes_to_keep = [selected_course] + prerequisites + unlocks
        filtered_subgraph.add_nodes_from(nodes_to_keep)
        edges_to_keep = (
            [(p, selected_course) for p in prerequisites if course_graph.has_edge(p, selected_course)] +
            [(u, v) for u, v in course_graph.edges() if u in nodes_to_keep and v in nodes_to_keep]
        )
        filtered_subgraph.add_edges_from(edges_to_keep)
    else:
        # Case 2: 8 or more direct neighbors, show prerequisites + neighbors
        nodes_to_keep = [selected_course] + prerequisites + direct_neighbors
        filtered_subgraph.add_nodes_from(nodes_to_keep)
        edges_to_keep = (
            [(p, selected_course) for p in prerequisites if course_graph.has_edge(p, selected_course)] +
            [(selected_course, n) for n in direct_neighbors if course_graph.has_edge(selected_course, n)]
        )
        filtered_subgraph.add_edges_from(edges_to_keep)

    return filtered_subgraph, prerequisites

def draw_edges(graph, pos, ax):
    for (u, v) in graph.edges():
        # Curve if same x but different y
        if pos[u][0] == pos[v][0] and pos[u][1] != pos[v][1]:
            rad = 0.3 if pos[u][1] < pos[v][1] else 0.3
            style = f"arc3,rad={rad}"
        else:
            style = "arc3,rad=0"
            
        nx.draw_networkx_edges(
            graph,
            pos,
            edgelist=[(u, v)],
            edge_color="gray",
            arrows=True,
            arrowsize=20,
            min_target_margin=20,
            connectionstyle=style,
            ax=ax
        )

# Function to visualize graph
# parent: where the graph is going to be displayed 
# subgraph: the unlocked_courses graph
# selected_course: the center of the graph
# onclick: onclick function passed to the node
def visualize_graph(parent, course_graph, selected_course, on_click):
    # Create a frame for the graph
    graph_frame = tk.Frame(parent)
    graph_frame.pack_propagate(False)
    graph_frame.pack(fill="both", expand=True, padx=0, pady=0)
    
    # Create the filtered subgraph
    filtered_subgraph, prerequisites = create_filtered_graph(course_graph, selected_course)

    # unlocks for node_colors
    unlocks = list(filtered_subgraph.successors(selected_course))

    # Create a matplotlib figure with a larger size for the graph content
    fig, ax = plt.subplots(figsize=(15, 10))
    pos = custom_layout(filtered_subgraph, selected_course, prerequisites)

    # Node colors
    node_colors = []
    for node in filtered_subgraph.nodes():
        if node == selected_course:
            node_colors.append("lightsteelblue")  # Course
        elif node in prerequisites:
            node_colors.append("salmon")          # Prereqs 
        elif node in unlocks:
            node_colors.append("lightgreen")      # unlocks
        else:
            node_colors.append("lightgray")

    # Dynamic node size
    num_nodes = len(filtered_subgraph.nodes())
    node_size = max(400, 1500 - (num_nodes * 30))

    # Draw the graph
    nx.draw_networkx_nodes(filtered_subgraph, pos, alpha=0.8, node_color=node_colors, node_size=node_size, edgecolors='black', ax=ax)
    nx.draw_networkx_labels(filtered_subgraph, pos, font_size=10, ax=ax)
    draw_edges(filtered_subgraph, pos, ax)
    
    # Legend
    legend_elements = [
        mpatches.Patch(color="salmon", label="Prerequisite"),
        mpatches.Patch(color="lightsteelblue", label="Selected Course"),
        mpatches.Patch(color="lightgreen", label="Unlocked Course"),
        mpatches.Patch(color="lightgray", label="Other")
    ]

    ax.legend(handles=legend_elements, loc="upper right")

    # Embed matplotlib figure
    canvas = FigureCanvasTkAgg(fig, master=graph_frame)
    canvas.draw()
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(fill="both", expand=True)
    
    # Add navigation toolbar for panning
    toolbar = NavigationToolbar2Tk(canvas, graph_frame)
    toolbar.update()
    toolbar.pack(side=tk.TOP, fill=tk.X)
    
    canvas.mpl_connect("button_press_event", lambda event: canvas._tkcanvas.focus_set())
    canvas.toolbar.pan() 

    def on_node_click(event):
        if event.inaxes:
            click_x, click_y = event.xdata, event.ydata
            for node, (x, y) in pos.items():
                distance = ((x - click_x)**2 + (y - click_y)**2)**0.5
                if distance < 0.1:  # Threshold
                    # Close current popup and show new one
                    if parent is not None:
                        parent.destroy()
                    on_click(course_name=node)
                    break

    canvas.mpl_connect("button_press_event", on_node_click)
    canvas_widget.update_idletasks()   # Force Tk to layout
    canvas_widget.config(width=800, height=450)  # Explicit canvas size
    canvas.draw()

    # This ensures the frame doesn't collapse on low-DPI or early-render
    graph_frame.update_idletasks()
    graph_frame.config(width=800, height=450)  

    return graph_frame