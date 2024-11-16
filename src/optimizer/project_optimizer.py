# src/optimizer/project_optimizer.py

from openai import OpenAI
from src.utils.file_loader import FileLoader
from pathlib import Path
from typing import Dict, List, Union
import json

class ProjectOptimizer:
    def __init__(self, api_key: str):
        """Initialize with OpenAI API credentials."""
        self.client = OpenAI(api_key=api_key)
        self.projects = FileLoader.load_projects(Path('input/projects.json'))
        self.skills = FileLoader.load_skills(Path('input/skills.json'))

    def rank_projects(self, job_description: str) -> List[Dict]:
        """Rank projects based on job description"""
        try:
            prompt = f"""
            Given these projects and job description, rank the projects by relevance.
            Consider technical alignment, domain relevance, and skill match.
            
            Projects:
            {json.dumps(self.projects, indent=2)}
            
            Job Description:
            {job_description}
            
            For each project, return a JSON object with:
            - id: use the project's full title
            - relevance_score: 0-100
            - reason: brief explanation of ranking
            
            Return exactly 3 projects, sorted by relevance_score descending.
            Make sure to use the exact project titles as IDs.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            
            ranked_projects = json.loads(response.choices[0].message.content)
            
            # Validate that we're using titles as IDs
            for project in ranked_projects:
                if project.get('id') not in [p.get('title') for p in self.projects]:
                    raise ValueError(f"Invalid project ID returned: {project.get('id')}")
            
            return ranked_projects
            
        except Exception as e:
            raise Exception(f"Error ranking projects: {str(e)}")

    def extract_relevant_skills(self, job_description: str) -> Dict[str, Union[List[Dict], Dict[str, List[str]]]]:
        """Extract relevant skills from job description"""
        try:
            prompt = f"""
            Analyze this job description and extract:
            1. Technical skills required
            2. Domain knowledge needed
            3. Specific technologies mentioned
            4. Soft skills required
            
            Job description:
            {job_description}
            
            Format the response as JSON with these keys: 
            technical_skills, domain_knowledge, technologies, soft_skills
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            raise Exception(f"Error extracting skills: {str(e)}")
