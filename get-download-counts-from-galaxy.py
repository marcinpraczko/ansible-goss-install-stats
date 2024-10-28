#!/usr/bin/env python3
"""
This script fetches the download count of an Ansible role from Ansible Galaxy,
writes the count to a JSON file, and generates a bar chart of the download counts
for the last 30 days.
"""

import subprocess
import re
import json
import pandas as pd
import matplotlib.pyplot as plt
import logging
import jinja2
import argparse

from datetime import datetime

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
        download_count = int(match.group(1))
        logger.info("Download count fetched successfully: %d", download_count)
        return download_count
    else:
        logger.warning("Download count not found in output. Output was: %s", result.stdout)
        return None


def write_download_count_to_json(_download_count, filename='data/download_counts.json'):
    """
    Writes the download count to a JSON file with the current date and time.

    Args:
        _download_count (int): The download count to write.
        filename (str): The name of the JSON file to write to.
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

def load_and_prepare_data(json_filename):
    """
    Loads the JSON data and prepares the DataFrame for further processing.

    Args:
        json_filename (str): The name of the JSON file to read from.

    Returns:
        pd.DataFrame: The prepared DataFrame.
    """
    logger.info("Loading JSON data from file: %s", json_filename)
    with open(json_filename, 'r') as file:
        data = json.load(file)
    df = pd.DataFrame(data)

    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d').dt.strftime('%Y%m%d')

    today = datetime.now()
    last_30_days = pd.date_range(end=today, periods=30).strftime('%Y%m%d').tolist()
    last_30_days_df = pd.DataFrame(last_30_days, columns=['date'])

    # Determine the default value
    if not df.empty:
        oldest_value = df['download_count'].iloc[0]
    else:
        oldest_value = 0

    default_value = oldest_value if oldest_value != 0 else df['download_count'].mean()

    last_30_days_df['download_count'] = default_value

    # Merge the data frames correctly
    merged_df = pd.merge(last_30_days_df, df, on='date', how='left')
    merged_df['download_count'] = merged_df['download_count_y'].fillna(merged_df['download_count_x'])
    merged_df = merged_df[['date', 'download_count']]

    return merged_df


def calculate_statistics(merged_df):
    """
    Calculates the statistics needed for the bar chart.

    Args:
        merged_df (pd.DataFrame): The merged DataFrame.

    Returns:
        tuple: A tuple containing the total downloads and the maximum daily difference.
    """
    # Calculate the difference between consecutive days
    merged_df['download_diff'] = merged_df['download_count'].diff().fillna(0)

    # Calculate the total downloads (latest value)
    total_downloads = merged_df['download_count'].iloc[-1]

    # Calculate the maximum daily difference
    max_daily_diff = merged_df['download_diff'].max()

    return total_downloads, max_daily_diff


def generate_barchart(merged_df, total_downloads, max_daily_diff, svg_filename):
    """
    Generates a bar chart from the prepared DataFrame and statistics.

    Args:
        merged_df (pd.DataFrame): The prepared DataFrame.
        total_downloads (int): The total downloads.
        max_daily_diff (float): The maximum daily difference.
        svg_filename (str): The name of the SVG file to save the bar chart to.
    """
    logger.info("Generating bar chart and saving to file: %s", svg_filename)
    # Create a bar chart (size is in inches)
    fig, ax = plt.subplots(figsize=(15, 8))
    bars = ax.bar(merged_df['date'], merged_df['download_diff'], color='blue')

    ax.set_xticks(merged_df['date'][::2])
    ax.set_xticklabels(merged_df['date'][::2], rotation=45, ha='right')

    ax.set_xlabel('Date')
    ax.set_ylabel('Download Count Difference')
    ax.set_title('Download Count Differences for the Last 30 Days')

    # Add total downloads text to the top-left corner
    ax.text(0.05, 0.95, f'Total Downloads: {total_downloads}', transform=ax.transAxes,
            fontsize=12, verticalalignment='top', horizontalalignment='left', bbox=dict(facecolor='white', alpha=0.5))

    # Add max downloads per day text below total downloads
    ax.text(0.05, 0.90, f'Max downloads per day: {max_daily_diff}', transform=ax.transAxes,
            fontsize=12, verticalalignment='top', horizontalalignment='left', bbox=dict(facecolor='white', alpha=0.5))

    # Add values on top of each bar
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height, f'{int(height)}', ha='center', va='bottom', color='blue')

    plt.tight_layout()
    plt.savefig(svg_filename, format='svg')
    plt.close()
    logger.info("Bar chart saved as SVG file: %s", svg_filename)


def create_barchart_from_json(json_filename='download_counts.json', svg_filename='download_counts.svg'):
    """
    Creates a bar chart from the download counts stored in a JSON file, showing the difference between consecutive days.

    Args:
        json_filename (str): The name of the JSON file to read from.
        svg_filename (str): The name of the SVG file to save the bar chart to.
    """
    merged_df = load_and_prepare_data(json_filename)
    total_downloads, max_daily_diff = calculate_statistics(merged_df)
    generate_barchart(merged_df, total_downloads, max_daily_diff, svg_filename)


def generate_html_from_template(image_url, generated_date, description,
                                template_path='templates/download_stats_page.html.j2',
                                output_path='docs/index.html'):
    """
    Generates an HTML page using a Jinja2 template.

    Args:
        image_url (str): The URL of the image to display.
        generated_date (str): The date when the image was generated.
        description (str): A description of what the image presents.
        template_path (str): The path to the Jinja2 template file.
        output_path (str): The path to save the generated HTML file.
    """
    logger.info("Generating HTML page from template: %s", template_path)

    # Load the Jinja2 template
    with open(template_path) as file:
        template = jinja2.Template(file.read())

    # Render the template with the provided data
    html_content = template.render(image_url=image_url,
                                   generated_date=generated_date,
                                   description=description)

    # Save the rendered HTML to a file
    with open(output_path, 'w') as file:
        file.write(html_content)

    logger.info("HTML page generated and saved to: %s", output_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process download counts.')
    parser.add_argument('--fetch', action='store_true', help='Fetch the download count from Ansible Galaxy')
    args = parser.parse_args()

    if args.fetch:
        download_count = get_download_count()
        if download_count is not None:
            write_download_count_to_json(download_count)
        else:
            logger.error("Download count not available.")
            exit(1)

    create_barchart_from_json(json_filename='data/download_counts.json',
                              svg_filename='docs/download_counts.svg')
    generate_html_from_template(image_url='download_counts.svg',
                                generated_date=datetime.now().strftime('%Y-%m-%d %H:%M'),
                                description='Download Counts for the Last 30 Days')
