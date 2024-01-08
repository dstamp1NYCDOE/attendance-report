import pandas as pd

import re

period_regex = re.compile(r"\d{1,2}")


def main(data):
    attendance_marks_filename = f"data/attendance.csv"
    attendance_marks_df = pd.read_csv(attendance_marks_filename)

    students_df = attendance_marks_df[
        ["StudentID", "LastName", "FirstName"]
    ].drop_duplicates()

    periods_df = attendance_marks_df[["Period"]].drop_duplicates()
    periods_df["Pd"] = periods_df["Period"].apply(return_pd)

    attendance_marks_df = attendance_marks_df.merge(
        periods_df, on=["Period"], how="left"
    )
    ## keep classes during the school day
    attendance_marks_df = attendance_marks_df[
        (attendance_marks_df["Pd"] > 0) & (attendance_marks_df["Pd"] < 10)
    ]

    ## courses to exclude
    courses_to_exclude = ["MQS21"]
    attendance_marks_df = attendance_marks_df[
        ~attendance_marks_df["Course"].isin(courses_to_exclude)
    ]

    pvt_by_student_by_date = pd.pivot_table(
        attendance_marks_df,
        index=["StudentID", "Date"],
        columns="Type",
        values="Pd",
        aggfunc=["min", "count"],
    ).fillna(-1)
    pvt_by_student_by_date.columns = [
        "_".join(col).strip() for col in pvt_by_student_by_date.columns.values
    ]

    pvt_by_student_by_date["is_present"] = pvt_by_student_by_date.apply(
        return_if_present, axis=1
    )

    pvt_by_student_by_date["is_late"] = pvt_by_student_by_date.apply(
        return_if_late_to_school, axis=1
    )

    pvt_by_student_by_date = pvt_by_student_by_date.reset_index()
    pvt_by_student_by_date["first_period_present"] = pvt_by_student_by_date[
        "min_present"
    ]
    cols = [
        "StudentID",
        "Date",
        "first_period_present",
        "is_present",
        "is_late",
    ]
    pvt_by_student_by_date_df = pvt_by_student_by_date[cols]

    ## determine potential cuts
    attendance_marks_df = attendance_marks_df.merge(
        pvt_by_student_by_date_df, on=["StudentID", "Date"], how="left"
    )
    attendance_marks_df["potential_cut"] = attendance_marks_df.apply(
        return_potential_cut, axis=1
    )

    ## running_attd_by_period
    cols = [
        "StudentID",
        "Date",
        "Course",
        "Type",
        "Pd",
        "Teacher",
        "potential_cut",
    ]
    period_attd_df = attendance_marks_df[cols]
    period_attd_df["present_in_class"] = period_attd_df["Type"].apply(
        lambda x: x in ["present", "tardy"]
    )
    period_attd_df["late_to_class"] = period_attd_df["Type"].apply(
        lambda x: x in ["tardy"]
    )

    ## attendance by period by date by students
    attendance_grid = (
        pd.pivot_table(
            period_attd_df,
            index=["StudentID", "Date"],
            columns="Pd",
            values="Type",
            aggfunc="first",
        )
        .fillna("")
        .reset_index()
    )

    period_attd_df = period_attd_df.merge(
        attendance_grid, on=["StudentID", "Date"], how="left"
    )

    period_attd_df = period_attd_df.merge(students_df, on=["StudentID"], how="left")

    period_attd_df["Date"] = pd.to_datetime(period_attd_df["Date"])
    
    return period_attd_df


def return_potential_cut(row):
    Pd = row["Pd"]
    type = row["Type"]
    is_present = row["is_present"]
    first_period_present = row["first_period_present"]

    potential_cut = (
        (type == "unexcused") and (is_present) and (Pd >= first_period_present)
    )
    return potential_cut


def return_if_late_to_school(pvt_row):
    is_present = pvt_row["is_present"]

    if not is_present:
        return False

    present = pvt_row["min_present"]
    tardy = pvt_row["min_tardy"]
    unexcused = pvt_row["min_unexcused"]

    if tardy < present and tardy > 0:
        return True
    if unexcused < present and unexcused > 0:
        return True

    return False


def return_if_present(pvt_row):
    present = pvt_row["count_present"]
    tardy = pvt_row["count_tardy"]
    total_present_marks = present + tardy
    return total_present_marks >= 2


def return_pd(period):
    mo = period_regex.search(period)
    return int(mo.group())


if __name__ == "__main__":
    data = {}

    main(data)
