#!/usr/bin/env python3
"""
This script fetches the download count of an Ansible role from Ansible Galaxy,
writes the count to a JSON file, and generates a bar chart of the download counts
for the last 30 days.
"""
import os.path
import subprocess
import re
import json
import pandas as pd
import matplotlib.pyplot as plt
import logging
import jinja2
import argparse

from datetime import datetime, timedelta

# Configure the root logger to suppress logs from external libraries
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
# Create a logger for your script
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_download_count():
    """
    Fetches the download count of the Ansible role 'marcinpraczko.goss-install' from Ansible Galaxy.

    Returns:
        int: The download count if found, otherwise None.
    """
    logger.info("Fetching download count from Ansible Galaxy.")
    try:
        result = subprocess.run(
            ["ansible-galaxy", "role", "info", "marcinpraczko.goss-install"],
            capture_output=True, text=True, check=True
        )
    except subprocess.CalledProcessError as e:
        logger.error("Error running ansible command: %s", e.stderr)
        return None

    match = re.search(r"download_count:\s+(\d+)", result.stdout)
    if match:
        _download_count = int(match.group(1))
        logger.info("Download count fetched successfully: %d", _download_count)
        return _download_count
    else:
        logger.warning("Download count not found in output. Output was: %s", result.stdout)
        return None

# TODO: Move this to class - will help debug exports to CSV when required
def export_df_to_csv(df, csv_file):
    """
    Exports a DataFrame to a CSV file using semicolons as delimiters.

    Args:
        df (pd.DataFrame): The DataFrame to export.
        csv_file (str): Path to save the CSV file.
    """
    logger.info(f"Exporting DataFrame to CSV file: {csv_file}")
    try:
        # Export the DataFrame to a CSV file with semicolons as delimiters
        df.to_csv(csv_file, index=False, sep=';')
        logger.info("CSV file created successfully.")
    except Exception as e:
        logger.error("Error exporting DataFrame to CSV: %s", e)

def write_download_count_to_json(_download_count, filename):
    """
    Writes the download count to a JSON file with the current date and time.

    Args:
        _download_count (int): The download count to write.
        filename (str): The name of the JSON file to write to.

    Raises:
        FileNotFoundError: If the JSON file does not exist and needs to be created.
    """
    logger.info("Writing download count to JSON file: %s", filename)
    current_date = datetime.now().strftime('%Y%m%d')
    data = {
        'date': current_date,
        'download_count': _download_count
    }

    try:
        with open(filename, 'r+') as file:
            file_data = json.load(file)
            # Check if a record with the current date exists
            for record in file_data:
                if record['date'] == current_date:
                    record['download_count'] = _download_count
                    break
            else:
                file_data.append(data)
            file.seek(0)
            json.dump(file_data, file, indent=4)
        logger.info("Download count written to existing JSON file.")
    except FileNotFoundError:
        with open(filename, 'w') as file:
            json.dump([data], file, indent=4)
        logger.info("JSON file not found. Created new JSON file and wrote download count.")


def create_barchart_from_df(df, svg_file, total_downloads, x_column, y_column, title, x_label, y_label, exclude_total=True):
    """
    Creates a bar chart from a DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame containing the data.
                           It should have at least the specified x_column and y_column.
        svg_file (str): The path to save the generated SVG file.
        total_downloads (int): The total downloads to display as a text annotation on the chart.
        x_column (str): The column to use for the x-axis.
        y_column (str): The column to use for the y-axis.
        title (str): The title of the bar chart.
        x_label (str): The label for the x-axis.
        y_label (str): The label for the y-axis.
        exclude_total (bool): Whether to exclude rows with 'Total Result' in the x_column (default is True).

    Raises:
        ValueError: If the DataFrame does not contain the specified x_column or y_column.
    """
    logger.info(f"Generating bar chart for {title} and saving to file: {svg_file}")

    # Optionally remove the 'Total Result' row
    if exclude_total:
        df = df[df[x_column] != 'Total Result']

    # Create a bar chart
    fig, ax = plt.subplots(figsize=(15, 8))
    bars = ax.bar(df[x_column], df[y_column].astype(int), color='blue')

    # Set chart labels and title
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)

    # Rotate x-axis labels for better readability
    ax.set_xticks(df[x_column])
    ax.set_xticklabels(df[x_column], rotation=45, ha='right')

    # Add values on top of each bar
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height, f'{height}', ha='center', va='bottom', fontsize=10)

    # Add total downloads text to the top-left corner
    ax.text(0.05, 0.95, f'Total Downloads: {total_downloads}', transform=ax.transAxes,
            fontsize=12, verticalalignment='top', horizontalalignment='left', bbox=dict(facecolor='white', alpha=0.5))

    # Save the bar chart as an SVG file
    plt.tight_layout()
    plt.savefig(svg_file, format='svg')
    plt.close()
    logger.info(f"Bar chart saved as SVG file: {svg_file}")

class Processing:
    """
    A class to handle processing of JSON, CSV, Excel, and pivot table operations.
    """

    def __init__(self, logger):
        """
        Initializes the Processing class with a logger.

        Args:
            logger (logging.Logger): The logger instance to use for logging.
        """
        self.logger = logger

    def convert_json_to_csv(self, json_file, csv_file, display=False):
        """
        Converts a JSON file to a CSV file.

        Args:
            json_file (str): Path to the JSON file.
            csv_file (str): Path to save the CSV file.
            display (bool): Whether to display the contents of the CSV file after creation (default is False).
        """
        self.logger.info("Converting JSON file to CSV")
        self.logger.info(f"  JSON file: {json_file}")
        self.logger.info(f"  CSV file: {csv_file}")
        try:
            # Load JSON data
            with open(json_file, 'r') as file:
                data = json.load(file)

            # Convert JSON data to a pandas DataFrame
            df = pd.DataFrame(data)

            # Write the DataFrame to a CSV file
            df.to_csv(csv_file, index=False, sep=';')
            self.logger.info("CSV file created successfully.")

            # Optionally display the contents of the CSV file
            if display:
                self.logger.info("Displaying contents of the CSV file:")
                print(df.to_string(index=False))
        except Exception as e:
            self.logger.error("Error converting JSON to CSV: %s", e)

    def convert_csv_to_excel(self, csv_file, excel_file):
        """
        Converts a CSV file to an Excel file.

        Args:
            csv_file (str): Path to the CSV file.
            excel_file (str): Path to save the Excel file.
        """
        self.logger.info("Converting CSV file to Excel")
        self.logger.info(f"  CSV file: {csv_file}")
        self.logger.info(f"  Excel file: {excel_file}")
        try:
            # Read the CSV file into a pandas DataFrame
            df = pd.read_csv(csv_file, sep=';')

            # Write the DataFrame to an Excel file
            df.to_excel(excel_file, index=False, sheet_name='Download Counts')
            self.logger.info("Excel file created successfully.")
        except Exception as e:
            self.logger.error("Error converting CSV to Excel: %s", e)

    def read_excel(self, excel_file):
        """
        Reads an Excel file into a pandas DataFrame.

        Args:
            excel_file (str): Path to the Excel file.

        Returns:
            pd.DataFrame: The DataFrame containing the data from the Excel file.
        """
        self.logger.info(f"Reading Excel file: {excel_file}")
        try:
            df = pd.read_excel(excel_file)
            self.logger.info("Excel file read successfully.")
            return df
        except Exception as e:
            self.logger.error("Error reading Excel file: %s", e)
            return pd.DataFrame()

    def generate_dfs_with_summary(self, df):
        """
        Generates daily and monthly summaries from the DataFrame.

        Args:
            df (pd.DataFrame): The DataFrame containing the data.

        Returns:
            tuple: A tuple containing:
                - last_download_count (int): The last value of the 'download_count' column.
                - df_daily_downloads (pd.DataFrame): DataFrame with daily downloads.
                - pt_monthly_downloads (pd.DataFrame): DataFrame summarizing monthly downloads.
        """
        self.logger.info("Generating monthly summary.")
        try:
            # Ensure the 'date' column is parsed correctly
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')

            # Extract the 'month_year' column in the desired format
            df['month_year'] = df['date'].dt.strftime('%Y/%m')
            df = df.sort_values(by='date')

            # Get the last value of the 'download_count' column
            last_download_count = df['download_count'].iloc[-1]
            self.logger.info(f"Last download count: {last_download_count}")

            # Calculate the daily downloads
            self.logger.info("Creating DataFrame with daily downloads.")
            df['daily_downloads'] = df['download_count'].diff().fillna(0).astype(int)
            df_daily_downloads = df[['date', 'daily_downloads']]
            df_daily_downloads = df_daily_downloads.rename(columns={'daily_downloads': 'Daily downloads'})
            df_daily_downloads = df_daily_downloads.reset_index()

            # Filter the DataFrame to include only the last 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)
            df_daily_downloads = df_daily_downloads[df_daily_downloads['date'] >= thirty_days_ago]

            # Create a pivot table to sum download counts by month_year
            self.logger.info("Creating pivot table for monthly downloads.")
            pt_monthly_downloads = df.pivot_table(
                index='month_year',
                values='daily_downloads',
                aggfunc='sum',
                margins=True,  # Add a "Total" row
                margins_name='Total Result'  # Name for the "Total" row
            )
            pt_monthly_downloads = pt_monthly_downloads.rename(columns={'daily_downloads': 'Monthly downloads'})
            pt_monthly_downloads = pt_monthly_downloads.sort_values(by='month_year')
            pt_monthly_downloads = pt_monthly_downloads.reset_index()

            self.logger.info("Monthly summary generated successfully.")
            return last_download_count, df_daily_downloads, pt_monthly_downloads
        except Exception as e:
            self.logger.error("Error generating monthly summary: %s", e)
            return 0, pd.DataFrame(), pd.DataFrame()

if __name__ == '__main__':
    svg_filename_daily_last30 = 'docs/download_counts_daily.svg'
    svg_filename_monthly = 'docs/download_counts_monthly.svg'
    json_filename = 'data/download_counts.json'
    csv_file = 'data/download_counts.csv'
    excel_file = 'data/download_counts.xlsx'

    parser = argparse.ArgumentParser(description='Process download counts.')
    parser.add_argument('--fetch', action='store_true', help='Fetch the download count from Ansible Galaxy')
    args = parser.parse_args()

    if args.fetch:
        download_count = get_download_count()
        if download_count is not None:
            write_download_count_to_json(download_count, json_filename)
        else:
            logger.error("Download count not available.")
            exit(1)

    processing = Processing(logger)
    processing.convert_json_to_csv(json_filename, csv_file)
    processing.convert_csv_to_excel(csv_file, excel_file)

    # Read Excel and generate monthly summary
    df = processing.read_excel(excel_file)
    total_download, df_daily, df_monthly = processing.generate_dfs_with_summary(df)

    # Generate bar charts
    # create_barchart_from_json(json_file=json_filename, svg_file=svg_filename_daily_last30)
    create_barchart_from_df(
        df=df_daily,
        svg_file=svg_filename_daily_last30,
        total_downloads=total_download,
        x_column='date',
        y_column='Daily downloads',
        title='Daily Download Counts for the Last 30 Days',
        x_label='Date',
        y_label='Download Count'
    )

    create_barchart_from_df(
        df=df_monthly,
        svg_file='docs/download_counts_monthly.svg',
        total_downloads=total_download,
        x_column='month_year',
        y_column='Monthly downloads',
        title='Monthly Download Counts',
        x_label='Month/Year',
        y_label='Download Count'
    )
