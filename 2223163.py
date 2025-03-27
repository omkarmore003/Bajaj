import pandas as pd
import re

def run():
    # Load datasets
    file_path = "C:/Users/Lenovo/OneDrive/Desktop/Data Engineering/data - sample.xlsx"
    attendance_df = pd.read_excel(file_path, sheet_name="Attendance_data")
    students_df = pd.read_excel(file_path, sheet_name="Student_data")

    # Convert attendance_date to datetime
    attendance_df['attendance_date'] = pd.to_datetime(attendance_df['attendance_date'])

    # Function to find students absent for more than 3 consecutive days
    def find_absence_streaks(df):
        df = df[df['status'] == 'Absent'].copy()
        streaks = []

        for student_id, group in df.groupby('student_id'):  # Ensure correct column name
            group = group.sort_values('attendance_date')
            group['gap'] = group['attendance_date'].diff().dt.days.ne(1).cumsum()
            max_streak = group.groupby('gap')['attendance_date'].agg(['min', 'max', 'count']).reset_index()
            max_streak = max_streak[max_streak['count'] > 3].tail(1)  # Get latest streak

            for _, row in max_streak.iterrows():
                streaks.append({
                    'student_id': student_id,
                    'absence_start_date': row['min'].strftime('%d-%m-%Y'),
                    'absence_end_date': row['max'].strftime('%d-%m-%Y'),
                    'total_absent_days': row['count']
                })

        return pd.DataFrame(streaks)

    # Find absence streaks
    absence_streaks_df = find_absence_streaks(attendance_df)

    # Merge with students data
    students_df = students_df.rename(columns={'studentid': 'student_id'})  # Ensure correct column name
    merged_df = absence_streaks_df.merge(students_df, on='student_id', how='left')

    # Validate emails
    def is_valid_email(email):
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*@[a-zA-Z]+\.(com)$', str(email)))

    merged_df['email'] = merged_df['parent_email'].apply(lambda x: x if is_valid_email(x) else None)

    # Generate message for valid emails
    def generate_message(row):
        return (f"Dear Parent, your child {row['student_name']} was absent from {row['absence_start_date']} "
                f"to {row['absence_end_date']} for {row['total_absent_days']} days. Please ensure their attendance improves.")

    merged_df['msg'] = merged_df.apply(lambda row: generate_message(row) if pd.notna(row['email']) else '', axis=1)

    # Select final columns
    final_output = merged_df[['student_id', 'absence_start_date', 'absence_end_date', 'total_absent_days', 'email', 'msg']]

    return final_output

# Run function
if __name__ == "__main__":
    result_df = run()
    print(result_df)
