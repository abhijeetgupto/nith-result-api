from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pymongo import MongoClient
import scrapper
import os
from scrapping_info import currently_enrolled, batches_enrolled, branches, branch_code, branch_code_18

from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

connection_string = os.getenv('MONGO_CONNECTION_STRING')
password = os.getenv('PASSWORD')

client = MongoClient(connection_string)
db = client.nith_results
# print(list(db.students.find({"roll": "195536"}))[0])


@app.get("/")
def index():
    return {"message": "Welcome To NIT-H Result API"}


@app.get("/students")
async def get_all_students():
    students_collection = db.ranked
    cursor = students_collection.find({}, {
        "_id": 0,
        "roll": 1,
        "name": 1,
        "department": 1,
        "cgpi": 1,
        "semester": 1,
        "rank": 1,
        "branch_rank": 1,
        "batch_rank": 1,
    })
    return list(cursor)


@app.get("/student/{roll_number}")
async def get_student_data(roll_number):
    students_collection = db.ranked
    details = list(students_collection.find({'roll': roll_number}))
    if details:
        detail = details[0]
        detail.pop("_id")
        return detail

    return {"error": "Incorrect RollNumber or Data not fetched yet"}


@app.delete("/remove_student/{pwd}/{roll_number}")
async def remove_student(pwd, roll_number):
    if pwd == password:
        students_collection = db.students
        result = students_collection.delete_one({"roll": roll_number})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Student not found")
        return {
            "message": "Student deleted successfully, "
                       "details will still be visible."
                       "Hit 'sort' endpoint to remove"
        }
    else:
        return {"error": "incorrect password"}


@app.delete("/remove_batch/{pwd}/{year}")
async def remove_batch(pwd, year):
    if pwd == password:
        students_collection = db.students
        result = students_collection.delete_many({"roll": {"$regex": "^" + year}})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Invalid batch code")
        return {
            "message": f"Details of batch's roll number starting with $^{year} deleted successfully."
                       "details will still be visible."
                       "Hit 'sort' endpoint to remove"
        }

    return {"error": "incorrect password"}


@app.post("/add_student/{pwd}/{branch}/{roll}")
async def add_student(pwd, roll, branch):
    if branch not in branches:
        print(branch)
        return {"error": "incorrect branch"}

    if pwd == password:
        batch = roll[:2]
        link = f"http://results.nith.ac.in/scheme{batch}/studentresult/index.asp"
        student_detail = scrapper.scrap_result(link, roll, branch)
        if "error" not in student_detail:

            students_collection = db.students
            # delete if it is already present in the db
            students_collection.delete_one({"roll": roll})
            students_collection.insert_one(student_detail)
            return {
                "message": "student added successfully"
                           "details won't be visible untill you hit 'sort' endpoint"
            }
        else:
            return student_detail

    return {"error": "incorrect password"}


@app.put("/sort/{pwd}")
async def rank_students(pwd):
    if pwd == password:
        # college_rank
        # class_rank
        # branch_rank
        ranks = {
            "college_rank": 1,

            "181": 1,
            "182": 1,
            "183": 1,
            "184": 1,
            "1845": 1,
            "185": 1,
            "1855": 1,
            "186": 1,
            "187": 1,
            "188": 1,

            "191": 1,
            "192": 1,
            "193": 1,
            "194": 1,
            "1945": 1,
            "195": 1,
            "1955": 1,
            "196": 1,
            "197": 1,
            "198": 1,

            "20bce": 1,
            "20bee": 1,
            "20bme": 1,
            "20bec": 1,
            "20dec": 1,
            "20bcs": 1,
            "20dcs": 1,
            "20bar": 1,
            "20bch": 1,
            "20bms": 1,
            "20bma": 1,
            "20bph": 1,

            "21bce": 1,
            "21bee": 1,
            "21bme": 1,
            "21bec": 1,
            "21dec": 1,
            "21bcs": 1,
            "21dcs": 1,
            "21bar": 1,
            "21bch": 1,
            "21bms": 1,
            "21bma": 1,
            "21bph": 1,

            "22bce": 1,
            "22bee": 1,
            "22bme": 1,
            "22bec": 1,
            "22dec": 1,
            "22bcs": 1,
            "22dcs": 1,
            "22bar": 1,
            "22bch": 1,
            "22bms": 1,
            "22bma": 1,
            "22bph": 1,

            "civil": 1,
            "electrical": 1,
            "mechanical": 1,
            "ece": 1,
            "eced": 1,
            "cse": 1,
            "csed": 1,
            "architecture": 1,
            "chemical": 1,
            "material": 1,
            "mnc": 1,
            "physics": 1,
        }

        students_collection = db.students
        cursor = list(students_collection.find({}))

        if not cursor:
            collection = db.ranked
            collection.drop()
            return {"message": "There are no documents in this collection now!"}

        cursor.sort(key=lambda x: -x["cgpi"])
        new = []
        for student in cursor:

            student["points_awarded"] = int(student["results"][-1]["cgpi_total"])
            student["points_total"] = int(((student["results"][-1]["cgpi"].split("="))[0].split("/"))[1]) * 10

            student["rank"] = ranks["college_rank"]
            student["branch_rank"] = ranks[student["department"]]
            ranks["college_rank"] += 1
            ranks[student["department"]] += 1

            batch = student["roll"][:4]
            if batch not in ranks:
                batch = student["roll"][:3]

            student["batch_rank"] = ranks[batch]
            ranks[batch] += 1
            new.append(student)

        collection = db.ranked
        collection.drop()
        db.ranked.insert_many(new)
        return {"status": "Sorted Successfully"}

    return {"error": "incorrect password"}

# ---------- This is to automate scraping as well, will implement it later.--------------- #
# ---------- Making post the complete batch at once is not possible because of the time limit thing ---- #
# ---------- So instead of that call the api for post method one by one for each student ------ #
# ---------- Therefore write a new script that post it one by one -------- #

# @app.put("/update_results/{pwd}/{batch}/{branch}/{start_roll}/{end_roll}")
# async def update_results(pwd, batch, branch, start_roll, end_roll):
#     if pwd == password:
#
#         # ------"curr" format-------
#         # batch_no->
#         #    department->
#         #       department_name
#         #    roll->
#         #        [start_roll, end_roll]
#
#         if batch not in batches_enrolled:
#             return {"error": "Check batch number"}
#
#         if branch not in branches:
#             return {"error": "Check branch"}
#
#         if batch == "18" or batch == "19":
#             roll_prefix = batch + branch_code_18[branch]
#         else:
#             roll_prefix = batch + branch_code[branch]
#
#         curr = currently_enrolled
#
#         if batch not in curr:
#             return {"error": "Invalid Batch"}
#
#         link = f"http://results.nith.ac.in/scheme{batch}/studentresult/index.asp"
#         start_roll = int(start_roll)
#         end_roll = int(end_roll)
#         for roll in range(start_roll, end_roll+1):
#             roll = str(roll)
#             if branch
#             student_info = scrap_result(branch, )
#
#
#     else:
#         return {"error": "incorrect password"}
