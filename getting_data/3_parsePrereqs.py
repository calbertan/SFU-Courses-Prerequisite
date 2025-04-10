import pandas as pd
  
all_courses = pd.read_csv("1_sfu_courses.csv")
prereqs = pd.read_csv("sfu_prereq.csv")

## merge prereqs with all_courses
df = pd.merge(
    all_courses,
    prereqs,
    on=['Department', 'CourseNumber'],
    how='left'  # Keeps all rows from df1 even if no match in df2
)

# Replace NaN values in Prerequisites and ParsedPrerequisites with 'N/A'
df['Prerequisites'] = df['Prerequisites'].fillna('N/A')
df['ParsedPrerequisites'] = df['ParsedPrerequisites'].fillna('N/A')

# Count # of offerings
df['numberOfOfferings'] = df['Offerings'].str.strip("[]").str.split(",").str.len()

# Format Offerings and Parsed Prerequisites to remove brackets and quotes
df['Offerings'] = df['Offerings'].apply(lambda x: ', '.join(eval(x)) if isinstance(x, str) and x.startswith('[') else 'N/A')
df['Simple Prerequisites'] = df['ParsedPrerequisites'].apply(lambda x: ', '.join(sorted(set(x.replace('(', '').replace(')', '').split(',')))) if isinstance(x, str) else 'N/A')

# Rename columns
df.rename(columns={
    "CourseNumber": "Course Number",
    "ParsedPrerequisites": "Parsed Prerequisites",
    "numberOfOfferings": "Number of Offerings"
}, inplace=True)

df.to_csv('../sfu_courses_dataset.csv', index=False)

print(df)