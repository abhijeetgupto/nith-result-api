from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup



def scrap_result(result_url, roll_number, department):

    try:
        option = webdriver.ChromeOptions()
        option.add_argument("--headless")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=option)
        driver.get(result_url)

        text_field = driver.find_element(By.NAME, "RollNumber")
        text_field.send_keys(roll_number)

        submit_button = driver.find_element(By.NAME, "B1")
        submit_button.click()

        soup = BeautifulSoup(driver.page_source, "lxml")
        # Find all rows
        rows = soup.find_all('tr')

        # Print out the data from each row
        cells = rows[1].find_all('td')
        personal_data = [cell.text.split("\n") for cell in cells]
        name = personal_data[1][2].strip()
        father_name = personal_data[2][2].strip()

        semester_result = []
        sem = {}
        sub = []

        for i in range(2, len(rows) - 1):
            row = rows[i]
            cells = row.find_all('td')
            row_data = [cell.text for cell in cells]
            if len(row_data) == 1:
                sem["subjects"] = sub
                semester_result.append(sem)
                sem = {"sem_no": row_data[0].split(":")[-1].strip()}
                sub = []

            elif len(row_data) == 5:
                sem["sgpi"] = row_data[1].replace("\n", "").split()[-1]
                sem["sgpi_total"] = row_data[2].replace("\n", "").split()[-1]
                sem["cgpi"] = row_data[3].replace("\n", "").split()[-1].replace("CGPI", "")
                sem["cgpi_total"] = row_data[4].replace("\n", "").split()[-1]

            elif len(row_data) == 6:
                curr = {"sno": int(row_data[0]),
                        "name": row_data[1].strip(),
                        "grade": row_data[4].strip(),
                        "points": int(row_data[5])
                        }
                sub.append(curr)

        sem["subjects"] = sub
        semester_result.append(sem)
        semester_result.pop(0)

        student = {
            "roll": roll_number,
            "department": department,
            "semester": int(semester_result[-1]["sem_no"][1:]) + 1,
            "name": name,
            "father_name": father_name,
            "cgpi": float(semester_result[-1]["cgpi"].split("=")[-1]),
            "results": semester_result,
        }
        return student
    except Exception as e:
        return {"error": str(e)}


# for testing purpose on local system

# def upload_to_database(url, start_roll, end_roll, department):
#     for roll_number in range(start_roll, end_roll + 1):
#         try:
#             student_data = scrap_result(url, str(roll_number), department)
#             collection.insert_one(student_data)
#             print(f"Done for {roll_number}")
#         except:
#             print(f"Unable to scrap {roll_number}")
#             continue
#


# client = pymongo.MongoClient("mongodb://localhost:27017")
# db = client["nith_results_data"]
# collection = db["final_year"]
# upload_to_database("http://results.nith.ac.in/scheme18/studentresult/index.asp", 181001, 194580, "material")
