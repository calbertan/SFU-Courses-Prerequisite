import pandas as pd

# current sfu_prereq only contains CMPT
  
all_courses = pd.read_csv("1_sfu_courses.csv")
prereqs = pd.read_csv("sfu_prereq.csv")

combined_df = pd.merge(
    all_courses,
    prereqs,
    on=['Department', 'CourseNumber'],
    how='left'  # Keeps all rows from df1 even if no match in df2
)

# Count # of offerings
combined_df['numberOfOfferings'] = combined_df['Offerings'].str.strip("[]").str.split(",").str.len()

combined_df.to_csv('3_sfu_courses_dataset.csv', index=False)

print(combined_df)