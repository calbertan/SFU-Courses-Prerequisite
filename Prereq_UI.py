import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import ttk
import ctypes
import networkx as nx
import matplotlib.pyplot as plt
import re
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from Graph import custom_layout, get_graph, visualize_graph

# Improve display quality on Windows
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

# Load dataset
file_path = "sfu_courses_dataset.csv"
df = pd.read_csv(file_path)

completed_courses = pd.read_csv("completed_courses.csv")
completed_set = set(zip(completed_courses['Department'], completed_courses['Course Number']))
df['has_completed'] = df.apply(
    lambda row: (row['Department'], row['Course Number']) in completed_set,
    axis=1
)

df['Parsed Prerequisites'] = df['Parsed Prerequisites'].fillna('No Prerequisites')  # Replace NaN
df['Parsed Prerequisites'] = df['Parsed Prerequisites'].apply(
    lambda x: 'N/A' if str(x).strip() == '' else x
)

df['Prerequisites'] = df['Prerequisites'].fillna('No Prerequisites')  # Replace NaN
df['Prerequisites'] = df['Prerequisites'].apply(
    lambda x: 'N/A' if str(x).strip() == '' else x
)

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

# Track current filter state
current_filter = "all"  # can be "all", "completed", or "not_completed"

def get_course_level(course_code):
    # Extract the first 3+ digits from the course code (e.g., "340" from "ACMA340")
    match = re.search(r'\d+', course_code)
    return int(match.group()) if match else 0  # Default to 0 if no number found

def can_take_course(prereq_str, completed_set):
    # Check if a course can be taken based on its parsed prerequisites and completed courses
    if prereq_str in ["No Prerequisites", "N/A"]:
        return True

    # Remove all whitespace and split into individual groups
    prereq_str = prereq_str.replace(" ", "")
    groups = prereq_str.split('),(')

    # Clean up parentheses
    groups = [group.strip('()') for group in groups if group.strip('()')]

    for group in groups:
        if not group:
            continue

        courses_in_group = group.split(',')
        all_completed = True

        for course in courses_in_group:
            match = re.match(r'([A-Za-z]+)(\d+[A-Za-z]*)', course)
            if match:
                dept, num = match.groups()
                try:
                    if (dept, int(num)) not in completed_set:
                        all_completed = False
                        break
                except ValueError:
                    all_completed = False
                    break
            else:
                all_completed = False
                break
        if all_completed:
            return True
    return False

def update_table():
    # Updates the table based on search input and current filter state
    global current_filter
    
    search_term = search_var.get().lower()
    for row in tree.get_children():
        tree.delete(row)

    # Apply filter first
    if current_filter == "completed":
        filtered_df = df[df['has_completed'] == True]
    elif current_filter == "not_completed":
        filtered_df = df[df['has_completed'] == False]
    elif current_filter == "can_take":
        # Filter for courses that can be taken based on prerequisites
        filtered_df = df[df['Parsed Prerequisites'].apply(
            lambda x: can_take_course(str(x), completed_set)
        )]
    else:
        filtered_df = df

    # Then apply search within filtered results
    for _, row in filtered_df.iterrows():
        # Create display values for only the columns we want to show
        display_values = [
            row['Department'],
            row['Course Number'],
            "Double-click for more detail",  # Prerequisites placeholder
            row['Offerings'],
            row['Parsed Prerequisites'],
            row['Number of Offerings'],
            "Yes" if row['has_completed'] else "No",  # Format completed status
            f"{row['Priority Score']:.1f}"
        ]
        if search_term in str(row['Department']).lower() or \
           search_term in str(row['Course Number']).lower() or \
           search_term in str(row['Prerequisites']).lower():
            tree.insert("", "end", values=display_values, tags=(row["Prerequisites"],))  # Store actual Prerequisites in tag

def set_filter(filter_type):
    # Sets the current filter and updates the table
    global current_filter
    current_filter = filter_type
    update_table()
    
    # Update button states to show which is active
    for btn in [all_button, completed_button, not_completed_button, can_take_button]:
        btn.config(relief=tk.RAISED)
    
    if filter_type == "all":
        all_button.config(relief=tk.SUNKEN)
    elif filter_type == "completed":
        completed_button.config(relief=tk.SUNKEN)
    elif filter_type == "not_completed":
        not_completed_button.config(relief=tk.SUNKEN)
    elif filter_type == "can_take":
        can_take_button.config(relief=tk.SUNKEN)

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
    if (pd.notna(row["Simple Prerequisites"])):
        course_name = f"{row['Department']}{row['Course Number']}"
        prerequisites = row["Simple Prerequisites"].split(", ")
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

def count_downward_prerequisites(course_graph, course_name):
    # Counts prerequisites recursively, only downward in course levels
    current_level = get_course_level(course_name)
    total_prereqs = 0
    visited = set()  # Avoid double-counting
    
    def _recursive_count(course):
        nonlocal total_prereqs
        for prereq in course_graph.predecessors(course):
            prereq_level = get_course_level(prereq)
            if prereq_level <= current_level and prereq not in visited:
                visited.add(prereq)
                total_prereqs += 1
                _recursive_count(prereq)  # Recurse downward
    
    _recursive_count(course_name)
    return total_prereqs

def calculate_priority_scores(df, course_graph):
    priority_scores = []
    for _, row in df.iterrows():
        course_name = f"{row['Department']}{row['Course Number']}"
        
        # Recursive downward prerequisites
        num_prereqs = count_downward_prerequisites(course_graph, course_name)
        
        # Number of unlocked courses
        num_unlocks = len(list(nx.descendants(course_graph, course_name)))
        
        # Offerings penalty
        try:
            offerings = max(float(row['Number of Offerings']), 1)
            inverse_offerings = 1 / offerings
        except:
            inverse_offerings = 0
        
        # Weighted score
        score = (0.35 * num_prereqs) + (0.5 * num_unlocks) + (0.15 * inverse_offerings)
        priority_scores.append(score)
    
    return priority_scores

# Add Priority Score column to DataFrame
df['Priority Score'] = calculate_priority_scores(df, course_graph)
df['Priority Score'] = df['Priority Score'].rank(pct=True) * 100

# ------------------------------- Tkinter UI -------------------------------
def link_unlocked_courses(popup_window, unlocked_courses):
    # Create a frame for the clickable courses with wrapping
    courses_frame = tk.Frame(popup_window)
    courses_frame.pack(fill="x", pady=5)
    
    # Track current row and column for grid layout
    current_row = 0
    current_col = 0
    max_cols = 30
    
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
    popup_window.geometry("1920x1080")

    label = tk.Label(popup_window, text=selected_course, font=("Arial", 14, "bold"))
    label.pack(padx=5, pady=5, anchor="w")

    # Prerequisites section
    label = tk.Label(popup_window, text="Prerequisites:", font=("Arial", 12, "bold"))
    label.pack(padx=5, anchor="w")
    
    if(actual_prerequisites == "N/A"):
        actual_prerequisites = "This course does not have prerequisites"
    
    prereq_text = tk.Label(popup_window, text=actual_prerequisites, wraplength=550, font=("Arial", 12), justify="left")
    prereq_text.pack(padx=5, pady=5, anchor="w")

    
    # Visualizing graph
    # Create a subgraph for the selected course and its descendants
    visualize_graph(popup_window, course_graph, selected_course, show_prerequisites)

# Create a frame for the filter buttons
filter_frame = tk.Frame(root)
filter_frame.pack(pady=10, anchor="w")

# Create filter buttons with toggle appearance
all_button = tk.Button(filter_frame, text="Show All", command=lambda: set_filter("all"), relief=tk.SUNKEN)
all_button.pack(side="left", padx=5)

completed_button = tk.Button(filter_frame, text="Show Completed", command=lambda: set_filter("completed"), relief=tk.RAISED)
completed_button.pack(side="left", padx=5)

not_completed_button = tk.Button(filter_frame, text="Show Not Completed", command=lambda: set_filter("not_completed"), relief=tk.RAISED)
not_completed_button.pack(side="left", padx=5)

can_take_button = tk.Button(filter_frame, text="Show Courses That Can Be Taken", command=lambda: set_filter("can_take"), relief=tk.RAISED)
can_take_button.pack(side="left", padx=5)

# Search bar
search_var = tk.StringVar()
search_entry = tk.Entry(root, textvariable=search_var, width=40)
search_entry.pack(pady=10)
search_button = tk.Button(root, text="Search", command=update_table)
search_button.pack(pady=5)
search_entry.bind('<Return>', lambda event: update_table())

# Table with Scrollbar
frame = tk.Frame(root)
frame.pack(expand=True, fill='both', pady=10)

scrollbar = ttk.Scrollbar(frame, orient="vertical")
columns_to_display = [col for col in df.columns if col != "Simple Prerequisites"]
tree = ttk.Treeview(frame, columns=columns_to_display, show='headings', yscrollcommand=scrollbar.set)
scrollbar.config(command=tree.yview)
scrollbar.pack(side="right", fill="y")
tree.pack(expand=True, fill='both')

# Adjust column widths
tree.heading("Department", text="Department")
tree.column("Department", width=30)

tree.heading("Course Number", text="Course Number")
tree.column("Course Number", width=65)

tree.heading("Prerequisites", text="Prerequisites")
tree.column("Prerequisites", width=155)

tree.heading("Offerings", text="Offerings")
tree.column("Offerings", width=460)

tree.heading("Parsed Prerequisites", text="Parsed Prerequisites")
tree.column("Parsed Prerequisites", width=400)

tree.heading("Number of Offerings", text="Number of Offerings")
tree.column("Number of Offerings", width=110)

tree.heading("has_completed", text="Completed")
tree.column("has_completed", width=25)

tree.heading("Priority Score", text="Priority Score")
tree.column("Priority Score", width=50)

style = ttk.Style()
style.configure("Treeview", rowheight=30)

tree.bind("<Double-1>", show_prerequisites)

update_table()

root.mainloop()