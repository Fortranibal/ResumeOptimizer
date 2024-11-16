# src/utils/file_loader.py

from pathlib import Path
import json

class FileLoader:
    @staticmethod
    def load_projects(filepath: str) -> list[dict]:
        """Load and parse projects from a JSON file."""
        with open(filepath, 'r') as f:
            projects = json.load(f)
        return projects

    @staticmethod
    def load_skills(filepath: str) -> dict[str, list[str]]:
        """Load and parse skills from a JSON file."""
        with open(filepath, 'r') as f:
            skills = json.load(f)
        return skills

    @staticmethod
    def load_job_description(filepath: str) -> str:
        """Load job description from a text file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            raise FileNotFoundError(f"Job description file not found at {filepath}")
        except Exception as e:
            raise Exception(f"Error reading job description: {str(e)}")
