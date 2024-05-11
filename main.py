import pandas as pd
import datetime
import os
import glob


def load_csv_file():
    csv_files = glob.glob('*.csv')
    if csv_files:
        print("Found the following CSV files:")
        for idx, file in enumerate(csv_files):
            print(f"{idx + 1}: {file}")
        file_index = input(
            "Enter the number of the CSV file you want to use, or specify a path: ")
        try:
            file_index = int(file_index) - 1
            if file_index >= 0 and file_index < len(csv_files):
                return csv_files[file_index]
        except ValueError:
            return file_index
    else:
        return input("No CSV files found in the current directory. Please enter the CSV file path: ")


# Get the current date and time
current_time = datetime.datetime.now()
formatted_time = current_time.strftime(
    "// Generated %d %B %H:%M\n// Go to https://sankeymatic.com/ to use this to generate your Sankey diagram\n")

# Load the CSV file
csv_path = load_csv_file()
df = pd.read_csv(csv_path)

# Normalize column data to title case
df['Outcome'] = df['Outcome'].str.title().fillna('Pending')
df['Who Applied?'] = df['Who Applied?'].str.title()

# Filter out 'Diary Update' from 'Outcome'
df = df[df['Outcome'] != 'Diary Update']

df['Application Exit'] = df['Application Exit'].str.title(
) if 'Application Exit' in df.columns else None
df['Screening Exit'] = df['Screening Exit'].str.title(
) if 'Screening Exit' in df.columns else None
df['First Interview Exit'] = df['First Interview Exit'].str.title(
) if 'First Interview Exit' in df.columns else None
df['Second Interview Exit'] = df['Second Interview Exit'].str.title(
) if 'Second Interview Exit' in df.columns else None

# Adjust processing logic if necessary


def determine_transition(row):
    if pd.notna(row['Screening Date']):
        return 'Screening'
    return row['Outcome']


# Apply normalization and count transitions
df['Application Exit'] = df.apply(determine_transition, axis=1)
df['Screening Exit'] = df.apply(lambda row: 'First Interview' if pd.notna(
    row['First Interview']) else row['Outcome'], axis=1)
df['First Interview Exit'] = df.apply(lambda row: 'Second Interview' if pd.notna(
    row['Second Interview']) else row['Outcome'], axis=1)
df['Second Interview Exit'] = df['Outcome']

# Count transitions and normalize outputs
application_summary = df['Application Exit'].value_counts().sort_index()
screening_summary = df.loc[pd.notna(
    df['Screening Date']), 'Screening Exit'].value_counts().sort_index()
first_interview_summary = df.loc[pd.notna(
    df['First Interview']), 'First Interview Exit'].value_counts().sort_index()
second_interview_summary = df.loc[pd.notna(
    df['Second Interview']), 'Second Interview Exit'].value_counts().sort_index()

# Who applied? summary
totals = df['Who Applied?'].value_counts()
who_applied_summary = ["I applied to them [{}] Application".format(count) if name == "Me"
                       else "They applied to me [{}] Application".format(count) for name, count in totals.items()]

# Formatting final output
final_output = [formatted_time] + (
    who_applied_summary +
    [f"Application [{count}] {exit}" for exit, count in application_summary.items()] +
    [f"Screening [{count}] {exit}" for exit, count in screening_summary.items()] +
    [f"First Interview [{count}] {exit}" for exit, count in first_interview_summary.items()] +
    [f"Second Interview [{count}] {exit}" for exit,
        count in second_interview_summary.items()]
)


# Write output to file
with open('sankeymatic_markup.txt', 'w') as file:
    for output in final_output:
        file.write(output + '\n')


# Print final formatted output
for output in final_output:
    print(output)
