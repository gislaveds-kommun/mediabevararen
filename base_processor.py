import os
import json
from abc import ABC, abstractmethod
from datetime import datetime
from utils import get_filter_date, transform_date, cleanup_folders_and_files


class BaseLocalProcessor(ABC):
    def __init__(self, config, output_dir, image_dir_constant, excel_path_constant, platform_name, config_key):
        self.config = config
        self.output_dir = output_dir
        self.excel_path = excel_path_constant
        self.platform_name = platform_name
        self.config_key = config_key
        self.image_dir = os.path.join(self.output_dir, image_dir_constant)

        self.is_date_comparison = False
        self.lower_date = datetime(1, 1, 1)
        self.upper_date = datetime.now()

    # -------------------------------------------------------------
    # 1. ABSTRACT REQUIREMENTS (Subclasses MUST implement these)
    # -------------------------------------------------------------
    @property
    @abstractmethod
    def relative_html_path(self):
        """Relative path to the HTML export file inside the export directory."""
        pass

    @abstractmethod
    def get_divide_choice(self):
        """Prompt user or pick filter/regex rules specific to this platform."""
        pass

    @abstractmethod
    def extract_and_save_posts(self, html_content):
        """Parse HTML soup specific to platform DOM structure and save results."""
        pass

    def save_config(self):
        """Persists changes back to config.json immediately on disk."""
        try:
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            print("Successfully updated config.json!")
        except Exception as e:
            print(f"Warning: Could not save config.json: {e}")

    def prompt_path_to_local_data(self):
        """Generic prompt to update local export path and save to disk."""
        current_path = self.config.get(self.config_key, "")

        # 1. If path is missing or empty, force the user to enter one
        if not current_path:
            print(f"\nNo path set for local {self.platform_name}.")
            while not current_path:
                current_path = input(f"Please enter the directory path for local {self.platform_name}: ").strip()

            self.config[self.config_key] = current_path
            self.save_config()

        # 2. If path already exists, ask if they want to change it
        else:
            print(f"\nYour current path to local {self.platform_name} is: {current_path}")
            answer = input(f"Do you want to update the path for {self.platform_name}? (y/n): ")
            if answer.lower() == "y":
                new_path = input(f"Enter new directory path for {self.platform_name}: ").strip()
                if new_path:
                    self.config[self.config_key] = new_path
                    self.save_config()

    def process(self):
        """Template method controlling execution sequence across all platforms."""
        self.prompt_path_to_local_data()

        local_path = self.config[self.config_key]
        self.base_path = f"file:///{local_path}/"
        self.html_file_path = os.path.join(local_path, self.relative_html_path)

        self.config['divider_regexp_pattern'] = self.get_divide_choice()

        # Shared Date Filtering Prompt
        lower = get_filter_date("lower")
        if lower:
            self.lower_date = transform_date(lower)
            self.is_date_comparison = True

        upper = get_filter_date("upper")
        if upper:
            self.upper_date = transform_date(upper)
            self.is_date_comparison = True
        else:
            self.upper_date = datetime.today().replace(hour=23, minute=59, second=59)

        if not os.path.exists(self.html_file_path):
            raise FileNotFoundError(f"HTML file not found at {self.html_file_path}")

        # PASS self.image_dir DIRECTLY HERE:
        cleanup_folders_and_files(self.output_dir, self.image_dir, self.excel_path)

        with open(self.html_file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()

        self.extract_and_save_posts(html_content)