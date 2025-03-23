import requests
import pandas as pd

# API endpoint
url = "https://api.sfucourses.com/v1/rest/outlines/all"

# Function to fetch and process course data
def fetch_courses(url):
    all_courses = []
    
    while url:
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            courses = data.get('data', [])
            
            # Extract relevant fields
            for course in courses:
                dept = course.get("dept", "")
                number = course.get("number", "")
                prereqs = course.get("prerequisites", "")
                
                # Ensure the course number is an integer
                try:
                    number = int(number)
                    all_courses.append({
                        "Department": dept,
                        "CourseNumber": number,
                        "Prerequisites": prereqs
                    })
                except ValueError:
                    continue
            
            # Handle pagination, get the next URL if available
            url = data.get('next_url', None)
        else:
            print(f"Failed to retrieve data: {response.status_code}")
            break
    
    return all_courses

# Fetch courses
courses = fetch_courses(url)

# Convert to DataFrame
df = pd.DataFrame(courses)

# Filter courses to 2-4th year
df = df[(df["CourseNumber"] < 500) & (df["CourseNumber"] > 100)]


# Display the DataFrame
print(df.head())

# Save to CSV for further use
df.to_csv("sfu_courses.csv", index=False)
print("✅ Data saved to sfu_courses.csv")
