ef visualize_graph(parent, course_graph, selected_course, on_click):
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
    return graph_frame