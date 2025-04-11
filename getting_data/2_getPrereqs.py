import re
import pandas as pd
# import ollama
# from io import StringIO

# client = ollama.Client()
# model = "llama3.2"

# Check if the prerequisites string contains a 3-digit number
def contains_course(prerequisites):
  if pd.isna(prerequisites):  # Check if the value is NaN
    return False
  return bool(re.search(r'\b\d{3}\b', prerequisites))
  
df = pd.read_csv("sfu_courses.csv")
df = df[df["Prerequisites"].map(contains_course)]
df.to_csv("2_sfu_courses_filtered.csv", index=False)

## Running local llm to parse data
# for dept, group in df.groupby('Department'):
#   # Convert the group to a CSV string
#   buffer = StringIO()
#   group.to_csv(buffer, index=False, header=False)
  
#   # Print the CSV string
#   dept_as_string = buffer.getvalue().strip()  # Strip to remove trailing newline

#   prompt = (
#     "Department,CourseNumber,Prerequisites"+
#     dept_as_string +
#     "\n " +
#     "I need you to create a ParsePrerequisite column that groups the prerequisites properly based on the AND/OR conditions. For example:\n" +
#     "'CMPT 225, (CMPT 295 or ENSC 254), and (CMPT 201 or ENSC 351) all with a minimum grade of C' becomes\n" +
#     "(CMPT225, CMPT295, CMPT201), (CMPT225, CMPT295, ENSC351), (CMPT225, ENSC254, CMPT201), (CMPT225, ENSC254, ENSC351)"
#   )
  
#   if(dept == "CMPT"):
#     response = client.generate(model=model, prompt=prompt)
#     print(response.response)
    # print(prompt)

