import pandas as pd
import process_attendance
import glob


def main(data):
    attendance_marks_filename = f"data/attendance.csv"
    attendance_marks_df = pd.read_csv(attendance_marks_filename)
    output_filename = f"output/{attendance_marks_df['Date'].min()}_{attendance_marks_df['Date'].max()}_attendance_report.xlsx"

    attd_errors_filename = f"output/{attendance_marks_df['Date'].min()}_{attendance_marks_df['Date'].max()}_attendance_errors.xlsx"

    period_attd_df = process_attendance.main(data)

    caass_swipes_filename = glob.glob(f"data/RPT*.csv")[0]
    caass_swipes_df = pd.read_csv(caass_swipes_filename)
    caass_swipes_df = caass_swipes_df[caass_swipes_df["Attendance Status"] != "Absent"]
    caass_swipes_df["Date"] = pd.to_datetime(caass_swipes_df["Entry Date"])
    caass_swipes_df["StudentID"] = caass_swipes_df["Student ID"]

    caass_swipes_df = caass_swipes_df[["StudentID", "Date", "Entry Time"]]

    period_attd_df = period_attd_df.merge(
        caass_swipes_df, on=["StudentID", "Date"], how="left"
    ).fillna("")

    writer = pd.ExcelWriter(output_filename)

    output_cols = [
        "StudentID",
        "LastName",
        "FirstName",
        "Date",
        "Entry Time",
        "Course",
        "Type",
        "Pd",
        "potential_cut",
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
    ]
    period_attd_df["Date"] = period_attd_df["Date"].apply(
        lambda x: x.strftime("%Y-%m-%d")
    )
    for teacher, df in period_attd_df.groupby("Teacher"):
        df = df.sort_values(by=["Pd", "Course", "LastName", "FirstName"])[output_cols]
        df.to_excel(writer, index=False, sheet_name=teacher)

    workbook = writer.book
    cut_format = workbook.add_format({"bg_color": "#FFC7CE", "font_color": "#9C0006"})
    period_format = workbook.add_format({"bold": True})
    no_caass_scan_format = workbook.add_format(
        {"bg_color": "#FFEB9C", "font_color": "#9C6500"}
    )
    for sheet in writer.sheets:
        worksheet = writer.sheets[sheet]
        worksheet.freeze_panes(1, 4)
        worksheet.autofit()

        worksheet.conditional_format(
            "A1:R1000",
            {"type": "formula", "criteria": "=$I1=True", "format": cut_format},
        )
        worksheet.conditional_format(
            "J1:R1000",
            {"type": "formula", "criteria": "=J$1=$H1", "format": period_format},
        )
        # worksheet.conditional_format(
        #     "A1:R1000",
        #     {"type": "formula", "criteria": '=$E1="" ', "format": no_caass_scan_format},
        # )
    writer.close()

    ## marked_present_or_on_time_without_caass_scan

    writer = pd.ExcelWriter(attd_errors_filename)
    df = period_attd_df[period_attd_df["Entry Time"] == ""]
    D75_students = df[df["Course"] == "ZJS11QB"]["StudentID"].unique()
    df = df[df["Type"].isin(["present", "tardy"])]
    df = df[~df["StudentID"].isin(D75_students)]

    for teacher, dff in df.groupby("Teacher"):
        dff = dff.sort_values(by=["Pd", "Course", "LastName", "FirstName"])[output_cols]
        dff.to_excel(writer, index=False, sheet_name=teacher)

    writer.close()
    return True


if __name__ == "__main__":
    data = {}
    main(data)


# # Light red fill with dark red text.
# format1 = workbook.add_format({"bg_color": "#FFC7CE", "font_color": "#9C0006"})

# # Light yellow fill with dark yellow text.
# format2 = workbook.add_format({"bg_color": "#FFEB9C", "font_color": "#9C6500"})

# # Green fill with dark green text.
# format3 = workbook.add_format({"bg_color": "#C6EFCE", "font_color": "#006100"})
