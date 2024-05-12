
import pandas as pd
import datetime
import os
import glob
import plotly.graph_objects as go


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


def create_sankey_df(application_summary, screening_summary, first_interview_summary, second_interview_summary):
    # Initialize lists to build DataFrame
    sources = []
    targets = []
    values = []

    # Application to Screening/Outcome
    for key, value in application_summary.items():
        sources.append('Application')
        targets.append(key)
        values.append(value)

    # Screening to First Interview/Outcome
    for key, value in screening_summary.items():
        sources.append('Screening')
        targets.append(key)
        values.append(value)

    # First Interview to Second Interview/Outcome
    for key, value in first_interview_summary.items():
        sources.append('First Interview')
        targets.append(key)
        values.append(value)

    # Second Interview to Outcome
    for key, value in second_interview_summary.items():
        sources.append('Second Interview')
        targets.append(key)
        values.append(value)

    return pd.DataFrame({'Source': sources, 'Target': targets, 'Value': values})


def generate_sankey_image(data, format='svg'):
    # Prepare data
    labels = list(set(data['Source']).union(set(data['Target'])))
    label_indices = {label: i for i, label in enumerate(labels)}

    # Create sources, targets, and values arrays for Plotly
    sources = data['Source'].map(label_indices).tolist()
    targets = data['Target'].map(label_indices).tolist()
    values = data['Value'].tolist()

    # Create the Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values
        ))])

    fig.update_layout(title_text="", font_size=10)
    filename = f'sankey_diagram.{format}'
    # Save as an image in the chosen format
    fig.write_image(filename)
    print(f"Sankey diagram saved as {filename}")


def output_picker(final_output):
    print("Select output format:")
    print("1: Console")
    print("2: Output file (sankeymatic_markup.txt)")
    print("3: Plotly diagram (Image)")
    choice = input("Enter choice (1, 2, or 3): ")

    if choice == '1':
        # Print to console
        for output in final_output:
            print(output)
    elif choice == '2':
        # Write to file
        with open('sankeymatic_markup.txt', 'w') as file:
            for output in final_output:
                file.write(output + '\n')
        print("Output written to sankeymatic_markup.txt.")
    elif choice == '3':
        # Choose image format for Plotly diagram
        print("Choose the image format:")
        print("1: SVG")
        print("2: PNG")
        print("3: JPG")
        format_choice = input("Enter choice (1, 2, or 3): ")
        format_dict = {'1': 'svg', '2': 'png', '3': 'jpg'}
        # Default to SVG if invalid choice
        format = format_dict.get(format_choice, 'svg')
        df_sankey = create_sankey_df(
            application_summary, screening_summary, first_interview_summary, second_interview_summary)
        generate_sankey_image(df_sankey, format)


# Main execution block
if __name__ == "__main__":
    output_picker(final_output)
