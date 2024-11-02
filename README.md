# Ansible Goss Install Stats

This project tracks the download statistics of the Ansible role `marcinpraczko.goss-install` and generates a webpage
displaying the stats.

## Overview

The download statistics are fetched from Ansible Galaxy using the Ansible Galaxy API. The statistics are stored in a JSON file.
The HTML page is generated and deployed to the `gh-pages` branch of the repository.

Idea behind this was to have quick automated way to track the download statistics of the Ansible role.

## Details about ansible role

- [Ansible Role: Goss Install](https://galaxy.ansible.com/ui/standalone/roles/marcinpraczko/goss-install/)
- [GitHub Repository: Goss Install](https://github.com/marcinpraczko/ansible-goss-install)

## Live Page

- [Download Statistics](https://marcinpraczko.github.io/ansible-goss-install-stats/)

## Motivation

The motivation behind this project was to track the download statistics of the Ansible role `marcinpraczko.goss-install`.
And present this in quick automated way by using only GitHub repository and GitHub Actions.

This is not ideal solution, but it is simple and works for the purpose - and not depends of any external services.

## Project Structure

- `templates/download_stats_page.html.j2`: Jinja2 template for generating the HTML page displaying the download statistics.
- `data/download_counts.json`: JSON file containing the download counts data.
- `.github/workflows/update-download-counts.yml`: GitHub Actions workflow for updating the download counts.

## Python Script

The Python script `get-download-counts-from-galaxy.py` fetches the latest download counts for the Ansible role
from Ansible Galaxy and updates the `data/download_counts.json` file. It also generates an HTML page using the Jinja2 template.

## Dependencies

Please install the dependencies using the following command:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## GitHub Actions Workflow

The GitHub Actions workflow `.github/workflows/update-download-counts.yml` is set up to run daily at 00:01 (UTC).
It performs the following steps:

1. Checks out the repository.
2. Sets up Python.
3. Installs the dependencies.
4. Generates a timestamp.
5. Runs the Python script to fetch the latest download counts and update the HTML page.
6. Commits and pushes the changes to the repository.
