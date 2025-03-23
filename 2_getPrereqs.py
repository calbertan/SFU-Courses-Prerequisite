import re
import pandas as pd

# Check if the prerequisites string contains a 3-digit number
def contains_course(prerequisites):
  if pd.isna(prerequisites):  # Check if the value is NaN
    return False
  return bool(re.search(r'\b\d{3}\b', prerequisites))
  
df = pd.read_csv("sfu_courses.csv")
df = df[df["Prerequisites"].map(contains_course)]

# Get sfu_prereq.csv, probably with LLMs
  
print(df)