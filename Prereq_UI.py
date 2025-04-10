import pandas as pd
import tkinter as tk
from tkinter import ttk
import ctypes
import networkx as nx
import matplotlib.pyplot as plt
import re
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

# Improve display quality on Windows
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

# Load dataset
file_path = "3_sfu_courses_dataset.csv"
df = pd.read_csv(file_path)

# Replace NaN values in Prerequisites and ParsedPrerequisites with 'N/A'
df['Prerequisites'] = df['Prerequisites'].fillna('N/A')
df['ParsedPrerequisites'] = df['ParsedPrerequisites'].fillna('N/A')

# Format Offerings and Parsed Prerequisites to remove brackets and quotes
df['Offerings'] = df['Offerings'].apply(lambda x: ', '.join(eval(x)) if isinstance(x, str) and x.startswith('[') else 'N/A')
df['ParsedPrerequisites'] = df['ParsedPrerequisites'].apply(lambda x: ', '.join(sorted(set(x.replace('(', '').replace(')', '').split(',')))) if isinstance(x, str) else 'N/A')

# Rename columns
df.rename(columns={
    "CourseNumber": "Course Number",
    "ParsedPrerequisites": "Parsed Prerequisites",
    "numberOfOfferings": "Number of Offerings"
}, inplace=True)

def on_close():
    print("Window closed")
    root.quit()

# Create the main window
root = tk.Tk()
root.protocol("WM_DELETE_WINDOW", on_close)
root.title("SFU Courses Viewer")
root.geometry("1920x1080")  # Set resolution to 1920x1080
root.option_add('*Font', 'Arial 12')  # Set a better font

# Global variable to track the pop-up window
popup_window = None

def update_table():
    """Updates the table based on search input."""
    search_term = search_var.get().lower()
    for row in tree.get_children():
        tree.delete(row)

    for _, row in df.iterrows():
        values = list(row)
        values[df.columns.get_loc("Prerequisites")] = "Double-click for more detail"  # Override Prerequisites display
        if search_term in str(row['Department']).lower() or \
           search_term in str(row['Course Number']).lower() or \
           search_term in str(row['Prerequisites']).lower():
            tree.insert("", "end", values=values, tags=(row["Prerequisites"],))  # Store actual Prerequisites in tag


# ------------------------------- Graph work -------------------------------
# Plan: courses = nodes, with directed edges = prerequisites


# Build course graph
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


# Returns list of courses that are unlocked by the given course
def get_unlocked_courses(course):
    if course in course_graph:
        unlocked = list(nx.descendants(course_graph, course))
        unlocked = sorted(unlocked)
        return unlocked # Returns all nodes reachable from course in course_graph 
    return []

# Function to visualize graph
# Function to visualize graph
def visualize_graph(parent, subgraph, selected_course):
    # Create a frame for the graph
    graph_frame = tk.Frame(parent)
    graph_frame.pack(fill="both", expand=True, pady=10)
    
    # Check the number of direct neighbors for the selected course
    direct_neighbors = list(subgraph.neighbors(selected_course))
    if len(direct_neighbors) > 5:
        nodes_to_keep = [selected_course] + direct_neighbors
        filtered_subgraph = nx.DiGraph()
        filtered_subgraph.add_nodes_from(nodes_to_keep)
        
        # Remove edges between neighbors (co-requisites ruin crowded graphs)
        edges_to_keep = [(u, v) for u, v in subgraph.edges() if u == selected_course and v in direct_neighbors]
        filtered_subgraph.add_edges_from(edges_to_keep)
    else:
        filtered_subgraph = subgraph

    # Create a matplotlib figure with a larger size for the graph content
    fig, ax = plt.subplots(figsize=(15, 10))
    pos = nx.spring_layout(filtered_subgraph, k=2, iterations=100)     
    node_colors = [
        "lightsteelblue" if node == selected_course else "lightgray"
        for node in filtered_subgraph.nodes()
    ]
     
    nx.draw_networkx_nodes(filtered_subgraph, pos, node_color=node_colors, node_size=1000, ax=ax)
    nx.draw_networkx_labels(filtered_subgraph, pos, font_size=10, ax=ax)
    nx.draw_networkx_edges(filtered_subgraph, pos, edge_color="gray", arrows=True, arrowsize=20, min_target_margin=20, ax=ax)

    # Embed matplotlib figure
    canvas = FigureCanvasTkAgg(fig, master=graph_frame)
    canvas.draw()
    canvas.get_tk_widget().config(width=600, height=300)
    canvas.get_tk_widget().pack(fill="both", expand=True)
    
    # Add navigation toolbar for panning
    toolbar = NavigationToolbar2Tk(canvas, graph_frame)
    toolbar.update()
    toolbar.pack(side=tk.TOP, fill=tk.X)
    canvas.mpl_connect("button_press_event", lambda event: canvas._tkcanvas.focus_set())
    canvas.toolbar.pan() 

    return graph_frame
# ------------------------------- Tkinter UI -------------------------------
def link_unlocked_courses(popup_window, unlocked_courses):
    # Create a frame for the clickable courses with wrapping
    courses_frame = tk.Frame(popup_window)
    courses_frame.pack(fill=tk.X, padx=20, pady=5)
    
    # Track current row and column for grid layout
    current_row = 0
    current_col = 0
    max_cols = 30  # Number of courses and commas per row
    
    for i, course in enumerate(unlocked_courses):
        # Create clickable label
        btn = tk.Label(courses_frame, text=course, fg="blue", cursor="hand2", 
                    font=("Arial", 11), padx=2)
        btn.grid(row=current_row, column=current_col, sticky="w")
        btn.bind("<Button-1>", lambda e, c=course: show_prerequisites(course_name=c))
        
        # Add hover effects
        btn.bind("<Enter>", lambda e, b=btn: b.config(fg="darkblue", font=("Arial", 11, "underline")))
        btn.bind("<Leave>", lambda e, b=btn: b.config(fg="blue", font=("Arial", 11)))
        
        current_col += 1
        
        # Add comma if not last in row
        if i < len(unlocked_courses) - 1 and current_col < max_cols:
            tk.Label(courses_frame, text=",", font=("Arial", 12)).grid(
                row=current_row, column=current_col, sticky="w")
            current_col += 1
        
        # Move to next row if needed
        if current_col >= max_cols:
            current_row += 1
            current_col = 0

def show_prerequisites(event=None, course_name=None):
    global popup_window  

    # Close existing pop-up if it's open
    if popup_window is not None:
        popup_window.destroy()
        popup_window = None

    if event is not None:
        # Case when called from table double-click
        selected_item = tree.selection()
        if selected_item:
            actual_prerequisites = tree.item(selected_item, "tags")[0]
            selected_course = tree.item(selected_item, "values")[0] + tree.item(selected_item, "values")[1]
    else:
        # Case when called from unlocked course click
        selected_course = course_name
        # Use regex to split letters and numbers
        import re
        match = re.match(r"([A-Za-z]+)(\d+[A-Za-z]*)", selected_course)
        if match:
            dept = match.group(1)
            num = match.group(2)
            # Convert both to strings and strip whitespace for comparison
            course_row = df[
                (df['Department'] == dept) & 
                (df['Course Number'].astype(str).str.strip() == num)
            ]
            actual_prerequisites = course_row.iloc[0]['Prerequisites'] if not course_row.empty else "N/A"
        else:
            actual_prerequisites = "N/A"

    unlocked_courses = get_unlocked_courses(selected_course)

    # Create popup window
    popup_window = tk.Toplevel(root)
    popup_window.title(f"Prerequisites for {selected_course}")
    popup_window.geometry("1000x800")

    label = tk.Label(popup_window, text=selected_course, font=("Arial", 14, "bold"))
    label.pack(padx=5, pady=5, anchor="w")

    # Prerequisites section
    label = tk.Label(popup_window, text="Prerequisites:", font=("Arial", 12, "bold"))
    label.pack(padx=5, anchor="w")
    
    if(actual_prerequisites == "N/A"):
        actual_prerequisites = "This course does not have prerequisites"
    
    prereq_text = tk.Label(popup_window, text=actual_prerequisites, wraplength=550, font=("Arial", 12), justify="left")
    prereq_text.pack(padx=5, pady=5, anchor="w")

    # Unlocked courses section
    unlocked_label = tk.Label(popup_window, text="This course unlocks:", font=("Arial", 12, "bold"))
    unlocked_label.pack(padx=5, anchor="w")
    
    if unlocked_courses:
       link_unlocked_courses(popup_window, unlocked_courses)
    else:
        unlocked_courses_text = "This course does not lock a higher level course"
        unlocked_text = tk.Label(popup_window, text=unlocked_courses_text, wraplength=550, font=("Arial", 12), justify="left")
        unlocked_text.pack(padx=5, anchor="w")
    
    # Visualizing graph
    # Create a subgraph for the selected course and its descendants
    subgraph_nodes = [selected_course] + unlocked_courses
    subgraph = course_graph.subgraph(subgraph_nodes)
    visualize_graph(popup_window, subgraph, selected_course)
    

# Search bar
search_var = tk.StringVar()
search_entry = tk.Entry(root, textvariable=search_var, width=40)
search_entry.pack(pady=10)
search_button = tk.Button(root, text="Search", command=update_table)
search_button.pack(pady=5)  # Added padding to move table down

# Table with Scrollbar
frame = tk.Frame(root)
frame.pack(expand=True, fill='both', pady=10)

scrollbar = ttk.Scrollbar(frame, orient="vertical")
tree = ttk.Treeview(frame, columns=list(df.columns), show='headings', yscrollcommand=scrollbar.set)
scrollbar.config(command=tree.yview)
scrollbar.pack(side="right", fill="y")
tree.pack(expand=True, fill='both')

# Adjust column widths
tree.heading("Department", text="Department")
tree.column("Department", width=25)

tree.heading("Course Number", text="Course Number")
tree.column("Course Number", width=45)

tree.heading("Prerequisites", text="Prerequisites")
tree.column("Prerequisites", width=150)

tree.heading("Offerings", text="Offerings")
tree.column("Offerings", width=500)

tree.heading("Parsed Prerequisites", text="Parsed Prerequisites")
tree.column("Parsed Prerequisites", width=500)

tree.heading("Number of Offerings", text="Number of Offerings")
tree.column("Number of Offerings", width=80)

style = ttk.Style()
style.configure("Treeview", rowheight=30)

tree.bind("<Double-1>", show_prerequisites)

update_table()

root.mainloop()
