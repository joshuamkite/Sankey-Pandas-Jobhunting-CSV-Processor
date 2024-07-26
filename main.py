import pandas as pd
import datetime
import glob
import plotly.graph_objects as go


def load_csv_file():
    """
    Search for and load a CSV file from the current directory.

    Returns:
        str: The path to the selected CSV file.
    """
    # Search for all CSV files in the current directory
    csv_files = glob.glob('*.csv')
    if csv_files:
        print("Found the following CSV files:")
        # Enumerate and display found CSV files
        for idx, file in enumerate(csv_files):
            print(f"{idx + 1}: {file}")
        file_index = input(
            "Enter the number of the CSV file you want to use, or specify a path: ")
        try:
            # Convert input to integer and select file
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

# Title case normalization for chosen header columns
df['Application Exit'] = df['Application Exit'].str.title(
) if 'Application Exit' in df.columns else None
df['Screening Exit'] = df['Screening Exit'].str.title(
) if 'Screening Exit' in df.columns else None
df['First Interview Exit'] = df['First Interview Exit'].str.title(
) if 'First Interview Exit' in df.columns else None
df['Second Interview Exit'] = df['Second Interview Exit'].str.title(
) if 'Second Interview Exit' in df.columns else None
df['Third Interview Exit'] = df['Third Interview Exit'].str.title(
) if 'Third Interview Exit' in df.columns else None


def determine_transition(row):
    """
    Determine the transition based on the screening date.

    Args:
        row (pd.Series): A row from the DataFrame.

    Returns:
        str: The determined transition.
    """
    # Determine the transition based on screening date being non null value
    if pd.notna(row['Screening Date']):
        return 'Screening'
    return row['Outcome']


# Apply transition determination across the DataFrame
df['Application Exit'] = df.apply(determine_transition, axis=1)
df['Screening Exit'] = df.apply(lambda row: 'First Interview' if pd.notna(
    row['First Interview']) else row['Outcome'], axis=1)
df['First Interview Exit'] = df.apply(lambda row: 'Second Interview' if pd.notna(
    row['Second Interview']) else row['Outcome'], axis=1)
df['Second Interview Exit'] = df.apply(lambda row: 'Third Interview' if pd.notna(
    row['Third Interview']) else row['Outcome'], axis=1)
df['Third Interview Exit'] = df['Outcome']

# Count and format transitions for various stages
application_summary = df['Application Exit'].value_counts().sort_index()
screening_summary = df.loc[pd.notna(
    df['Screening Date']), 'Screening Exit'].value_counts().sort_index()
first_interview_summary = df.loc[pd.notna(
    df['First Interview']), 'First Interview Exit'].value_counts().sort_index()
second_interview_summary = df.loc[pd.notna(
    df['Second Interview']), 'Second Interview Exit'].value_counts().sort_index()
third_interview_summary = df.loc[pd.notna(
    df['Third Interview']), 'Third Interview Exit'].value_counts().sort_index()

# Create summary based on 'Who Applied?' column
totals = df['Who Applied?'].value_counts()
who_applied_summary = ["I applied to them [{}] Application".format(count) if name == "Me"
                       else "They applied to me [{}] Application".format(count) for name, count in totals.items()]

# Compile all formatted outputs into one list
final_output = [formatted_time] + (
    who_applied_summary +
    [f"Application [{count}] {exit}" for exit, count in application_summary.items()] +
    [f"Screening [{count}] {exit}" for exit, count in screening_summary.items()] +
    [f"First Interview [{count}] {exit}" for exit, count in first_interview_summary.items()] +
    [f"Second Interview [{count}] {exit}" for exit, count in second_interview_summary.items()] +
    [f"Third Interview [{count}] {exit}" for exit,
        count in third_interview_summary.items()]
)


def create_sankey_df(application_summary, screening_summary, first_interview_summary, second_interview_summary, third_interview_summary):
    """
    Create a DataFrame for Sankey diagram data.

    Args:
        application_summary (pd.Series): Summary of application exits.
        screening_summary (pd.Series): Summary of screening exits.
        first_interview_summary (pd.Series): Summary of first interview exits.
        second_interview_summary (pd.Series): Summary of second interview exits.
        third_interview_summary (pd.Series): Summary of third interview exits.

    Returns:
        pd.DataFrame: DataFrame containing sources, targets, and values for the Sankey diagram.
    """
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

    # Second Interview to Third Interview/Outcome
    for key, value in second_interview_summary.items():
        sources.append('Second Interview')
        targets.append(key)
        values.append(value)

    # Third Interview to Outcome
    for key, value in third_interview_summary.items():
        sources.append('Third Interview')
        targets.append(key)
        values.append(value)

    return pd.DataFrame({'Source': sources, 'Target': targets, 'Value': values})


def generate_sankey_image(data, format='svg'):
    """
    Generate and save a Sankey diagram as an image.

    Args:
        data (pd.DataFrame): DataFrame containing sources, targets, and values for the Sankey diagram.
        format (str): The image format to save (default is 'svg').

    Returns:
        None
    """
    # Prepare data
    labels = list(set(data['Source']).union(set(data['Target'])))
    label_indices = {label: i for i, label in enumerate(labels)}

    # Create sources, targets, and values arrays for Plotly
    sources = data['Source'].map(label_indices).tolist()
    targets = data['Target'].map(label_indices).tolist()
    values = data['Value'].tolist()

    # Generate a list of colors with 50% opacity
    color_palette = [
        'rgba(166,206,227,0.5)',  # Pale Blue
        'rgba(31,120,180,0.5)',   # Strong Blue
        'rgba(178,223,138,0.5)',  # Pale Green
        'rgba(51,160,44,0.5)',    # Strong Green
        'rgba(251,154,153,0.5)',  # Pale Red
        'rgba(227,26,28,0.5)',    # Strong Red
        'rgba(253,191,111,0.5)',  # Pale Orange
        'rgba(255,127,0,0.5)',    # Strong Orange
        'rgba(202,178,214,0.5)',  # Pale Purple
        'rgba(106,61,154,0.5)',   # Strong Purple
        'rgba(255,255,153,0.5)',  # Light Yellow
        'rgba(177,89,40,0.5)',    # Dark Brown
        'rgba(0,0,0,0.5)',        # Black
        'rgba(177,179,0,0.5)'     # Olive
    ]

    # Cycle through the color palette if there are more links than colors
    link_colors = [color_palette[i % len(color_palette)]
                   for i in range(len(sources))]

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
            value=values,
            color=link_colors  # Apply the generated colors with opacity
        ))])

    fig.update_layout(title_text="", font_size=10)
    filename = f'sankey_diagram.{format}'
    # Save as an image in the chosen format
    fig.write_image(filename)
    print(f"Sankey diagram saved as {filename}")


def output_picker(final_output):
    """
    Allow the user to select the output format for the final result.

    Args:
        final_output (list): List of formatted output strings.

    Returns:
        None
    """
    print("Select output format:")
    print("1: Console")
    print("2: Output file (sankeymatic_markup.txt)")
    print("3: Plotly diagram (Image)")
    choice = input("Enter choice (1, 2, or 3): ")

    if (choice == '1'):
        # Print to console
        for output in final_output:
            print(output)
    elif (choice == '2'):
        # Write to file
        with open('sankeymatic_markup.txt', 'w') as file:
            for output in final_output:
                file.write(output + '\n')
        print("Output written to sankeymatic_markup.txt.")
    elif (choice == '3'):
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
            application_summary, screening_summary, first_interview_summary, second_interview_summary, third_interview_summary)
        generate_sankey_image(df_sankey, format)


# Main execution block
if __name__ == "__main__":
    output_picker(final_output)
