import pandas as pd
import tkinter as tk
from tkinter import ttk
import ctypes
import networkx as nx
import matplotlib.pyplot as plt
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
        return unlocked # Returns all nodes reachable from course in course_graph 
    return []

# Function to visualize graph
def visualize_graph(parent, subgraph, selected_course):
    # Create a frame for the graph
    graph_frame = tk.Frame(parent)
    graph_frame.pack(fill="both", expand=True, pady=10)

    # Create a matplotlib figure with a larger size for the graph content
    fig, ax = plt.subplots(figsize=(25, 10))
    pos = nx.spring_layout(subgraph, k=1.0, iterations=100)     
    node_colors = [
        "lightsteelblue" if node == selected_course else "lightgray"
        for node in subgraph.nodes()
    ]
     
    nx.draw_networkx_nodes(subgraph, pos, node_color=node_colors, node_size=1000, ax=ax)
    nx.draw_networkx_labels(subgraph, pos, font_size=10, ax=ax)
    nx.draw_networkx_edges( subgraph, pos, edge_color="black", arrows=True, alpha=0.4, ax=ax)

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

def show_prerequisites(event):
    global popup_window  

    # Close existing pop-up if it's open
    if popup_window is not None:
        popup_window.destroy()

    selected_item = tree.selection()
    if selected_item:
        actual_prerequisites = tree.item(selected_item, "tags")[0]  # Retrieve saved Prerequisites from tags
        selected_course = tree.item(selected_item, "values")[0] + tree.item(selected_item, "values")[1] # Retrieve course number

        unlocked_courses = get_unlocked_courses(selected_course)

        # Create a new popup window
        popup_window = tk.Toplevel(root)
        popup_window.title("Prerequisites Detail")
        popup_window.geometry("600x800")  # Increased size

        label = tk.Label(popup_window, text="Prerequisites:", font=("Arial", 14, "bold"))
        label.pack(pady=10)

        prereq_text = tk.Label(popup_window, text=actual_prerequisites, wraplength=550, font=("Arial", 12))
        prereq_text.pack(pady=10)

        unlocked_label = tk.Label(popup_window, text="This course unlocks:", font=("Arial", 14, "bold"))
        unlocked_label.pack(pady=10)

        unlocked_text = tk.Label(popup_window, text=unlocked_courses, wraplength=550, font=("Arial", 12))
        unlocked_text.pack(pady=10)
        
        # Visualizing graph
        # Create a subgraph for the selected course and its descendants
        subgraph_nodes = [selected_course] + unlocked_courses
        subgraph = course_graph.subgraph(subgraph_nodes)
        
        # Check density
        num_nodes = subgraph.number_of_nodes()

        # graph is too dense to display
        if num_nodes > 25:
            unlocked_label = tk.Label(popup_window, text="Graph too dense, just take the class", font=("Arial", 14, "bold"))
            unlocked_label.pack(pady=10)
        else:
            visualize_graph(popup_window, subgraph, selected_course)

        close_button = tk.Button(popup_window, text="Close", command=popup_window.destroy)
        close_button.pack(pady=10)

        # Ensure the pop-up is closed when destroyed
        popup_window.protocol("WM_DELETE_WINDOW", lambda: set_popup_none())

def set_popup_none():
    """Resets the global pop-up variable when the window is closed."""
    global popup_window
    popup_window = None

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
