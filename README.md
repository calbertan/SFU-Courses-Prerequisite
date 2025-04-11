# SFU-Courses-Prerequisite
Course planning is a critical part of academic success that students often overlook. While the SFU program has graduation requirements that can act as a general guideline, students still face challenges in understanding how their other courses may connect to future opportunities that are not mandatory for their program. Courses have clearly defined prerequisites, but there is not much information regarding what that class leads to. A lot of students only start properly planning once they are close to graduation, but you want to make sure that those classes you took on your second year as a random elective might actually lead to an interesting fourth year class.


## How to Run
1. Edit the completed_course.csv to include courses you have completed. They should be in the same format as what we have provided.

2. Run the Prereq_UI.py with the following command
```
python Prereq_UI.py
```

## How we retrieve data
Below are the steps we took to obtain the dataset, along with which programs to run.

1. **Run 1_getSFUCourses.py** to generate the initial **1_sfu_courses.csv**.

2. Run **2_getPrereqs.py** to filter simplify the dataset into **2_sfu_courses_filtered.csv**, removing  The reason we had this step seperated from step 1 is because initialy, it was intended that this step should run a local llm to parse the data, but we chose not to do that due to time constraints.

3. Use an llm to parse the 2_sfu_courses_filtered.csv. The prompt.txt was used to train the model to obtain the data that we needed, we copied the result returned by the llm to **sfu_prereq.csv**.

4. Do some final filtering and parsing by running **3_parsePrereq.py** to combine **1_sfu_courses.csv** and **sfu_prereq.csv** into **sfu_courses_dataset.csv** in the project's home directory. This is the final dataset that is used by our project.