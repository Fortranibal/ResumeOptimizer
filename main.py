# LLM Response Parser
import openai
from openai import OpenAI
from dotenv import load_dotenv
# Required for file I/O, JSON parsing, etc.
from pathlib import Path
import shutil
import os
import json
from typing import List, Dict, Union
import re
import subprocess
import datetime
# For visual print statements
from colorama import init, Fore, Back, Style
import time

class ResumeProjectOptimizer:
    """
    A class to analyze job descriptions and rank projects based on relevance.
    
    This class uses OpenAI's GPT-4 to perform intelligent analysis of job descriptions,
    extract relevant skills, and match them against a portfolio of projects.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the ResumeProjectOptimizer with OpenAI API credentials.
        
        Args:
            api_key (str): OpenAI API key for authentication
        """
        self.client = OpenAI(api_key=api_key)
        self.projects = self.load_projects(Path('input/projects.json'))
        self.skills = self.load_skills(Path('input/skills.json'))

    def load_projects(self, filepath: str) -> List[Dict]:
        """
        Load and parse projects from a JSON file.
        
        Args:
            filepath (str): Path to the JSON file containing project definitions
            
        Returns:
            List[Dict]: A list of project dictionaries containing project details
        """
        with open(filepath, 'r') as f:
            projects = json.load(f)
        return projects

    def load_skills(self, filepath: str) -> Dict[str, List[str]]:
        """
        Load and parse skills from a JSON file.
        
        Args:
            filepath (str): Path to the JSON file containing skills
            
        Returns:
            Dict[str, List[str]]: Dictionary of skill categories and their skills
        """
        with open(filepath, 'r') as f:
            skills = json.load(f)
        return skills


    def extract_relevant_skills(self, job_description: str) -> Dict[str, Union[List[Dict], Dict[str, List[str]]]]:
        """
        Analyze a job description to extract both explicit and implicit required skills.
        """
        prompt = f"""
        Analyze this job description and extract two categories of skills:
        1. Explicit skills: Directly mentioned in the description
        2. Implicit skills: Not directly mentioned but typically expected/valuable for this role

        Job Description:
        {job_description}

        For each skill, provide:
        - Relevance score (0-100)
        - Reason why it's important for the role
        - Whether it's explicit or implicit
        
        IMPORTANT: Respond with raw JSON only, no markdown formatting, no code blocks.

        Return as structured JSON with this exact format:
        {{
            "explicit_skills": [
                {{
                    "skill": "skill name",
                    "relevance": 85,
                    "reason": "brief explanation"
                }}
            ],
            "implicit_skills": [
                {{
                    "skill": "skill name",
                    "relevance": 75,
                    "reason": "brief explanation"
                }}
            ],
            "recommended_skill_section": {{
                "Languages": ["skill1", "skill2"],
                "Technologies": ["tech1", "tech2"],
                "Domain Knowledge": ["domain1", "domain2"]
            }}
        }}
        """

        try:
            print("Sending request to GPT...")
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo", #  gpt-4 is nice but pretty expensive (use gpt-4o-mini for testing)
                messages=[
                    {"role": "system", "content": "You are an expert ATS system analyzer that helps optimize resumes for job applications."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )

            print("\nReceived response from GPT")
            result = response.choices[0].message.content
            print("\nAttempting to parse JSON...")
            parsed_json = json.loads(result)
            print("Successfully parsed JSON")

            return json.loads(response.choices[0].message.content)

        except json.JSONDecodeError as e:
            print(f"\nJSON Decode Error: {str(e)}")
            print(f"Problematic response: {result}")
            raise Exception("Failed to parse GPT response into valid JSON")
        except Exception as e:
            print(f"\nUnexpected error: {str(e)}")
            raise


    def rank_projects(self, job_description: str) -> List[Dict]:
        """
        Rank projects based on their relevance to the job description.
        """
        print("\nStarting project ranking...")

        try:
            print("Extracting relevant skills...")
            relevant_skills = self.extract_relevant_skills(job_description)
            print("Successfully extracted skills")
        
            prompt = f"""
            Given the following:

            1. Job Description:
            {job_description}

            2. Identified Key Skills:
            {json.dumps(relevant_skills, indent=2)}

            3. Projects:
            {json.dumps(self.projects, indent=2)}

            Return a JSON array of the top 3 most relevant projects that best demonstrate the required skills.
            For each project include:
            1. project_id
            2. relevance_score (0-100)
            3. reason (2-3 sentences explaining why this project is relevant)
            4. demonstrated_skills (list of specific skills from the analysis that this project demonstrates)
            5. adaptation_suggestions (brief suggestions on how to emphasize certain aspects of this project for this specific job)

            IMPORTANT: Respond with raw JSON only, no markdown formatting, no code blocks.

            Format as valid JSON:
            [{{
                "project_id": "...",
                "relevance_score": XX,
                "reason": "...",
                "demonstrated_skills": ["skill1", "skill2", "skill3"],
                "adaptation_suggestions": "..."
            }}]
            """

            print("\nSending project ranking request to GPT...")
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional resume optimizer that helps match projects to job requirements."},
                    {"role": "user", "content": prompt}
                ]
            )

            print("\nReceived project ranking response")
            result = response.choices[0].message.content
            print("\nParsing ranking JSON...")
            parsed_json = json.loads(result)
            print("Successfully parsed ranking JSON")
            
            return parsed_json
        
        except Exception as e:
            print(f"\nError in rank_projects: {str(e)}")
            raise


    def load_job_description(self, filepath: str) -> str:
        """Load job description from a text file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            raise FileNotFoundError(f"Job description file not found at {filepath}")
        except Exception as e:
            raise Exception(f"Error reading job description: {str(e)}")

def main():
    # Initialize colorama
    init()

    print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}📝 Resume Optimizer Starting...{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}\n")

    # Load API key
    try:
        with open('.env', 'r') as f:
            env_contents = f.read()
            api_key = env_contents.split('=')[1].strip()
        print(f"{Fore.GREEN}✓ API key loaded successfully{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}✗ Error loading API key: {e}{Style.RESET_ALL}")
        return

    try:
        # Initialize optimizer
        optimizer = ResumeProjectOptimizer(api_key)
        print(f"{Fore.GREEN}✓ Resume Optimizer initialized{Style.RESET_ALL}")

        # Load job description
        job_description = optimizer.load_job_description('input/job_description.txt')
        print(f"{Fore.GREEN}✓ Job description loaded successfully!{Style.RESET_ALL}")

        print(f"\n{Fore.YELLOW}🔄 Analyzing job description...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
        
        # Extract relevant skills
        print(f"\n{Fore.YELLOW}📊 Extracting relevant skills...{Style.RESET_ALL}")
        relevant_skills = optimizer.extract_relevant_skills(job_description)
        
        # Rank projects
        print(f"\n{Fore.YELLOW}🏆 Ranking projects...{Style.RESET_ALL}")
        ranked_projects = optimizer.rank_projects(job_description)

        # Save results
        output = {
            "relevant_skills": relevant_skills,
            "ranked_projects": ranked_projects
        }
        
        output_path = Path('output/output.json')
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"\n{Fore.GREEN}✓ Results saved to {output_path}{Style.RESET_ALL}")

    except Exception as e:
        print(f"\n{Fore.RED}✗ Error: {str(e)}{Style.RESET_ALL}")
        # Save error output
        error_output = {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        with open('output/output.json', 'w') as f:
            json.dump(error_output, f, indent=2)
        raise

    print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✨ Process completed successfully!{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}\n")

if __name__ == "__main__":
    main()