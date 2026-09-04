import os
import shutil
from datetime import datetime
from urllib.parse import urlparse
import requests
import pandas as pd
from constants import CLI_STRINGS as cli


def is_valid_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def get_filter_date(date_type):

    match date_type:
        case "lower":
            answer_filter_date = input(cli['question_lower_date'])
        case "upper":
            answer_filter_date = input(cli['question_upper_date'])

    if answer_filter_date.lower() == "y":
        while True:
            filter_date = input(cli['question_get_filter_date'])
            if is_valid_date(filter_date):
                return filter_date
            else:
                print(cli['invalid_date_format'])
    else:
        return False


def transform_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d")


def translate_swedish_date(date_str):
    date_str = date_str.lower()
    months = {
        "januari": "Jan", "februari": "Feb", "mars": "Mar",
        "april": "Apr", "maj": "May", "juni": "Jun",
        "juli": "Jul", "augusti": "Aug", "september": "Sep",
        "oktober": "Oct", "november": "Nov", "december": "Dec",
        # Also handle short versions if they exist in your data
        "jan": "Jan", "feb": "Feb", "mar": "Mar", "apr": "Apr",
        "okt": "Oct", "dec": "Dec"
    }

    for swedish, english in months.items():
        if swedish in date_str:
            date_str = date_str.replace(swedish, english)
            break

    return date_str


def save_html(html_soup, save_path):
    with open(save_path, 'w', encoding='utf-8') as file:
        file.write(str(html_soup.prettify()))


def copy_local_image(full_img_url, image_dir, local_root_dir=None):
    local_path = urlparse(full_img_url).path
    if os.name == 'nt':
        local_path = local_path.lstrip('/')

    img_name = os.path.basename(local_path)
    dest_path = os.path.join(image_dir, img_name)
    
    if os.path.exists(local_path):
        try:
            shutil.copy(local_path, dest_path)
            print(f"Copied: {dest_path}")
            return True
        except Exception as e:
            print(f"Failed direct copy for {local_path}: {e}")

    if local_root_dir and os.path.exists(local_root_dir):
        for root, _, files in os.walk(local_root_dir):
            if img_name in files:
                found_path = os.path.join(root, img_name)
                try:
                    shutil.copy(found_path, dest_path)
                    print(f"Copied (found in subfolder): {dest_path}")
                    return True
                except Exception as e:
                    print(f"Failed fallback copy for {found_path}: {e}")

    print(f"Could not locate media file on disk: {img_name}")
    return False


def download_image(full_img_url, img_url, image_dir):
    try:
        response = requests.get(full_img_url, stream=True, timeout=30)
        response.raise_for_status()

        img_name = os.path.basename(img_url)
        img_path = os.path.join(image_dir, img_name)

        with open(img_path, 'wb') as img_file:
            for chunk in response.iter_content(1024):
                img_file.write(chunk)

        print(f"Downloaded: {img_path}")

    except Exception as e:
        print(f"Failed to download image {full_img_url}: {e}")


def save_extracted_data_to_file(extracted_data, excel_path):
    df = pd.DataFrame(extracted_data, columns=['Webbadress', 'Webbsida'])
    df.to_excel(excel_path, index=False)


def cleanup_folders_and_files(output_dir, image_dir, excel_path):
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
        
    # Recreate parent output directory
    os.makedirs(output_dir, exist_ok=True)

    # Clean up Excel file
    if os.path.exists(excel_path):
        os.remove(excel_path)
        print(f"Cleaned up existing Excel file: {excel_path}")

    # Recreate image directory directly inside parent output directory
    os.makedirs(image_dir, exist_ok=True)
    print(f"Prepared image directory: {image_dir}")
