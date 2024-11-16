# src/utils/file_loader.py

from pathlib import Path
import json
from typing import Dict, List, Union
import os

class FileLoader:
    @staticmethod
    def load_projects(filepath: str) -> List[Dict]:
        """
        Load and parse projects from a JSON file.
        
        Args:
            filepath (str): Path to the JSON file containing project definitions
            
        Returns:
            List[Dict]: A list of project dictionaries containing project details
            
        Raises:
            FileNotFoundError: If the projects file doesn't exist
            JSONDecodeError: If the JSON file is invalid
            Exception: For other errors during file loading
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Print debug information
                print(f"\nLoaded projects data type: {type(data)}")
                print(f"Data structure: {json.dumps(data, indent=2)[:200]}...")  # Show first 200 chars
                
                # Handle both direct list and nested dictionary formats
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and 'projects' in data:
                    return data['projects']
                else:
                    raise ValueError("Invalid projects data structure. Expected list or dict with 'projects' key")
                
        except FileNotFoundError:
            raise FileNotFoundError(f"Projects file not found at {filepath}")
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in projects file: {str(e)}", e.doc, e.pos)
        except Exception as e:
            raise Exception(f"Error loading projects: {str(e)}")

    @staticmethod
    def load_skills(filepath: str) -> Dict[str, List[str]]:
        """
        Load and parse skills from a JSON file.
        
        Args:
            filepath (str): Path to the JSON file containing skills
            
        Returns:
            Dict[str, List[str]]: Dictionary of skill categories and their skills
            
        Raises:
            FileNotFoundError: If the skills file doesn't exist
            JSONDecodeError: If the JSON file is invalid
            Exception: For other errors during file loading
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                skills = json.load(f)
                # Print debug information
                print(f"\nLoaded skills data type: {type(skills)}")
                print(f"Skills structure: {json.dumps(skills, indent=2)[:200]}...")  # Show first 200 chars
                return skills
        except FileNotFoundError:
            raise FileNotFoundError(f"Skills file not found at {filepath}")
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in skills file: {str(e)}", e.doc, e.pos)
        except Exception as e:
            raise Exception(f"Error loading skills: {str(e)}")

    @staticmethod
    def load_job_description(filepath: str) -> str:
        """
        Load job description from a text file.
        
        Args:
            filepath (str): Path to the text file containing the job description
            
        Returns:
            str: The job description text
            
        Raises:
            FileNotFoundError: If the job description file doesn't exist
            Exception: For other errors during file loading
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                # Print debug information
                print(f"\nLoaded job description length: {len(content)} characters")
                print(f"First 200 characters: {content[:200]}...")
                return content
        except FileNotFoundError:
            raise FileNotFoundError(f"Job description file not found at {filepath}")
        except Exception as e:
            raise Exception(f"Error reading job description: {str(e)}")

    @staticmethod
    def ensure_output_directory(base_dir: str = 'output') -> None:
        """
        Ensure the output directory exists.
        
        Args:
            base_dir (str): Base directory path for outputs
        """
        try:
            os.makedirs(base_dir, exist_ok=True)
            print(f"\nOutput directory ensured at: {base_dir}")
        except Exception as e:
            raise Exception(f"Error creating output directory: {str(e)}")

    @staticmethod
    def save_output(data: Dict, filepath: str) -> None:
        """
        Save output data to a JSON file.
        
        Args:
            data (Dict): Data to save
            filepath (str): Path where to save the file
            
        Raises:
            Exception: If there's an error saving the file
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"\nOutput saved successfully to: {filepath}")
        except Exception as e:
            raise Exception(f"Error saving output: {str(e)}")
