# import openai
from openai import OpenAI
from pathlib import Path
import shutil
import os
import json
from typing import List, Dict, Union
import re
import subprocess
from dotenv import load_dotenv

load_dotenv()

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
        self.projects = self.load_projects(Path('src/projects.json'))
        self.skills = self.load_skills(Path('src/skills.json'))

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

    def extract_achievements(self, description: str) -> List[str]:
        """Extract achievements and outcomes from project description"""
        achievements = []
        
        # Look for specific achievement indicators
        indicators = [
            (r'achieved.*?[\.\n]', 'achievement'),
            (r'improved.*?[\.\n]', 'improvement'),
            (r'reduced.*?[\.\n]', 'reduction'),
            (r'increased.*?[\.\n]', 'increase'),
            (r'developed.*?[\.\n]', 'development'),
        ]
        
        for pattern, _ in indicators:
            matches = re.finditer(pattern, description, re.IGNORECASE)
            achievements.extend([match.group(0).strip() for match in matches])
            
        return achievements

    def extract_keywords(self, description: str) -> List[str]:
        """Extract key technical terms and concepts from description"""
        keywords = []
        technical_terms = [
            "reinforcement learning", "CNN", "trajectory", "propulsion",
            "simulation", "control", "aerospace", "machine learning",
            "computer vision", "mining", "satellite", "rocket"
        ]
        for term in technical_terms:
            if term.lower() in description.lower():
                keywords.append(term)
        return keywords

    def extract_technologies(self, description: str) -> List[str]:
        """Extract specific technologies mentioned in description"""
        technologies = []
        tech_patterns = [
            "Python", "C++", "MATLAB", "TD3", "DDPG", "YOLOv7",
            "LaTeX", "STK", "GMAT", "EcoSimPro"
        ]
        for tech in tech_patterns:
            if tech in description:
                technologies.append(tech)
        return technologies

    def extract_metrics(self, description: str) -> Dict[str, str]:
        """Extract quantitative metrics from description"""
        metrics = {}
        metric_patterns = [
            (r'(\d+(?:\.\d+)?)\s*%', 'percentage'),
            (r'(\d+(?:\.\d+)?)\s*km/s', 'velocity'),
            (r'(\d+(?:\.\d+)?)\s*G', 'g_force'),
            (r'Mach\s*(\d+(?:\.\d+)?)', 'mach')
        ]
        
        for pattern, metric_type in metric_patterns:
            matches = re.findall(pattern, description)
            if matches:
                metrics[metric_type] = matches[0]
                
        return metrics
    

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

        Candidate's Current Skills:
        {json.dumps(self.skills, indent=2)}

        For each skill, provide:
        - Relevance score (0-100)
        - Reason why it's important for the role
        - Whether it's explicit or implicit
        
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
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert ATS system analyzer that helps optimize resumes for job applications."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )

            print("\nReceived response from GPT")
            result = response.choices[0].message.content
            print("\nGPT Response:")
            print(result)

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
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional resume optimizer that helps match projects to job requirements."},
                    {"role": "user", "content": prompt}
                ]
            )

            print("\nReceived project ranking response")
            result = response.choices[0].message.content
            print("\nGPT Response for ranking:")
            print(result)
            
            print("\nParsing ranking JSON...")
            parsed_json = json.loads(result)
            print("Successfully parsed ranking JSON")
            
            return parsed_json
        
        except Exception as e:
            print(f"\nError in rank_projects: {str(e)}")
            raise

    def update_latex_file(self, ranked_projects: List[Dict]):
        """
        Update the LaTeX file with the ranked projects.
        
        Args:
            ranked_projects: List of ranked project dictionaries
        """
        latex_path = 'src/resume.tex'
        
        with open(latex_path, 'r') as f:
            content = f.read()
            
        # Create new project order based on rankings
        project_order = [proj['project_id'] for proj in ranked_projects]
        
        # Update project order in LaTeX
        projects_section = r'% Begin Projects Section'
        for idx, project_id in enumerate(project_order):
            # Replace existing project command with new ordered version
            old_pattern = rf'\\project{project_id}'
            new_command = f'\\project{project_id}'
            content = content.replace(old_pattern, new_command)
            
        with open(latex_path, 'w') as f:
            f.write(content)

    def compile_pdf(self):
        """Compile the LaTeX file into a PDF"""
        try:
            # Run pdflatex twice to ensure references are properly updated
            subprocess.run(['pdflatex', 'src/resume.tex'], check=True)
            subprocess.run(['pdflatex', 'src/resume.tex'], check=True)
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error compiling PDF: {str(e)}")

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
    # Load OpenAI API key from environment
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("Please set OPENAI_API_KEY environment variable")

    # Initialize optimizer
    optimizer = ResumeProjectOptimizer(api_key)

    # Define path for job description
    job_desc_path = 'src/job_description.txt'

    # Check if job description file exists
    if not os.path.exists(job_desc_path):
        print(f"Please create {job_desc_path} with the job description and run again.")
        print("You can copy-paste the entire job posting into this file.")
        
        # Create empty file for user
        with open(job_desc_path, 'w', encoding='utf-8') as f:
            f.write("Paste job description here")
        
        return

    try:
        job_description = optimizer.load_job_description(job_desc_path)
        print("\nJob description loaded successfully!")
        print(f"Length: {len(job_description)} characters")
        
        # Extract skills and rank projects
        print("\nAnalyzing projects for best match...")
        ranked_projects = optimizer.rank_projects(job_description)
        
        print("\nTop 3 projects selected:")
        for proj in ranked_projects:
            print(f"\n- {proj['project_id']}")
            print(f"  Score: {proj['relevance_score']}")
            print(f"  Reason: {proj['reason']}")
            print(f"  Adaptation: {proj['adaptation_suggestions']}")

        # Update LaTeX
        optimizer.update_latex_file(ranked_projects)

        # Compile PDF
        optimizer.compile_pdf()
        
        print("\nDone! Your resume has been updated and recompiled.")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return

if __name__ == "__main__":
    main()