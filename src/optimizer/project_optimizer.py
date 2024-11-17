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
        self.content_weight = 0.5
        self.length_weight = 0.2
        self.keyword_weight = 0.3
        self.similarity_threshold = 0.4  # Lowered from previous value
        self.max_length_ratio = 2.5      # Increased tolerance for length difference

    def extract_relevant_skills(self, job_description: str) -> Dict[str, Union[List[Dict], Dict[str, List[str]]]]:
        """Extract unique and relevant skills from job description"""
        try:
            prompt = f"""
            Analyze this job description and extract relevant skills and requirements.
            Rules:
            1. Remove any duplicate skills (even if phrased differently)
            2. Combine similar skills into a single, most professional term
            3. Only include skills that are explicitly mentioned or clearly implied
            4. Use standardized industry terminology
            5. List skills in order of importance/relevance
            6. Ensure each skill appears in only one category
            
            Return the response in the following JSON format ONLY:
            {{
                "technical_skills": [
                    // Core technical competencies required for the role
                    // No duplicates across categories
                ],
                "domain_knowledge": [
                    // Specific industry/domain expertise
                    // Distinct from technical skills
                ],
                "technologies": [
                    // Specific tools, platforms, and software
                    // Use official/standard names
                ],
                "soft_skills": [
                    // Professional and interpersonal skills
                    // Only include explicitly mentioned ones
                ]
            }}

            Categorization Rules:
            - Technical Skills: Specific technical abilities and methodologies
            - Domain Knowledge: Industry-specific knowledge and concepts
            - Technologies: Concrete tools, platforms, and software
            - Soft Skills: Professional and interpersonal capabilities

            Examples:
            - If "Python programming" and "Python development" are mentioned, use only "Python"
            - If "thermal analysis" and "thermal simulation" appear, choose the more comprehensive term
            - Place "MATLAB" in technologies, not in technical_skills
            - Don't duplicate "system engineering" between technical_skills and domain_knowledge

            Job Description:
            {job_description}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a technical skills analyzer that ensures unique, relevant, and properly categorized skills extraction. Avoid any duplicates across categories."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,  # Low temperature for consistency
            )
            
            content = response.choices[0].message.content.strip()
            print(f"\nGPT Response:\n{content}")
            
            # Parse and validate the response
            try:
                skills_dict = json.loads(content)
                
                # Validate and clean the response
                cleaned_dict = {
                    category: list(set(skills))  # Remove any duplicates within categories
                    for category, skills in skills_dict.items()
                }
                
                # Check for duplicates across categories
                all_skills = []
                duplicates = []
                for category, skills in cleaned_dict.items():
                    for skill in skills:
                        if skill.lower() in [s.lower() for s in all_skills]:
                            duplicates.append(skill)
                        all_skills.append(skill)
                
                if duplicates:
                    print(f"\n{Fore.YELLOW}Warning: Found duplicate skills across categories: {duplicates}{Style.RESET_ALL}")
                
                # Validate required categories
                required_categories = ['technical_skills', 'domain_knowledge', 'technologies', 'soft_skills']
                for category in required_categories:
                    if category not in cleaned_dict:
                        cleaned_dict[category] = []
                
                return cleaned_dict
                
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {str(e)}")
                print(f"Received content: {content}")
                raise Exception("Failed to parse GPT response as JSON")
                
        except Exception as e:
            print(f"Error in skill extraction: {str(e)}")
            # Provide a fallback response
            return {
                "technical_skills": [],
                "domain_knowledge": [],
                "technologies": [],
                "soft_skills": []
            }


    def rank_projects(self, job_description: str) -> List[Dict]:
        """Rank projects based on job description"""
        try:
            prompt = f"""
            You are a technical recruiter analyzing project relevance. Return ONLY a JSON array of exactly 3 project rankings.

            Given these projects:
            {json.dumps(self.projects, indent=2)}
            
            And this job description:
            {job_description}

            Create a JSON array with exactly 3 objects in this format:
            [
                {{
                    "id": "exact_project_title",
                    "relevance_score": number_between_0_and_100,
                    "reason": "brief_explanation"
                }},
                {{
                    "id": "exact_project_title",
                    "relevance_score": number_between_0_and_100,
                    "reason": "brief_explanation"
                }},
                {{
                    "id": "exact_project_title",
                    "relevance_score": number_between_0_and_100,
                    "reason": "brief_explanation"
                }}
            ]

            Rules:
            1. Use EXACT project titles as IDs
            2. Include exactly 3 projects
            3. Score from 0-100
            4. Provide concise reasons
            5. Return ONLY the JSON array, no other text
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a JSON-output assistant that always returns valid JSON arrays. Never include additional text or explanations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
            )
            
            # Get and clean the response content
            content = response.choices[0].message.content.strip()
            
            # Debug information
            print(f"\nRaw GPT Response:\n{content}")
            
            try:
                # Try to parse the JSON response
                ranked_projects = json.loads(content)
                
                # Validate the response structure
                if not isinstance(ranked_projects, list):
                    raise ValueError("Response is not a JSON array")
                
                if len(ranked_projects) != 3:
                    raise ValueError(f"Expected 3 projects, got {len(ranked_projects)}")
                
                # Validate each project
                valid_titles = [p.get('title') for p in self.projects]
                for project in ranked_projects:
                    if not isinstance(project, dict):
                        raise ValueError("Project entry is not a dictionary")
                    
                    if 'id' not in project or 'relevance_score' not in project or 'reason' not in project:
                        raise ValueError("Project missing required fields")
                    
                    if project['id'] not in valid_titles:
                        raise ValueError(f"Invalid project ID: {project['id']}")
                    
                    if not isinstance(project['relevance_score'], (int, float)):
                        raise ValueError("Relevance score must be a number")
                    
                    if not (0 <= project['relevance_score'] <= 100):
                        raise ValueError("Relevance score must be between 0 and 100")
                
                return ranked_projects
                
            except json.JSONDecodeError as e:
                print(f"JSON Parse Error: {str(e)}")
                print(f"Problematic content:\n{content}")
                # Try to clean and repair common JSON issues
                try:
                    # Remove any leading/trailing text
                    content = content.strip()
                    if content.startswith('```json'):
                        content = content.split('```json')[1]
                    if content.endswith('```'):
                        content = content.rsplit('```', 1)[0]
                    content = content.strip()
                    return json.loads(content)
                except:
                    raise Exception("Failed to parse GPT response as JSON")
                    
        except Exception as e:
            print(f"Ranking Error: {str(e)}")
            # Provide a fallback ranking if possible
            if hasattr(self, 'projects') and self.projects:
                return [
                    {
                        "id": project.get('title', ''),
                        "relevance_score": 0,
                        "reason": "Fallback ranking due to error"
                    }
                    for project in self.projects[:3]
                ]
            raise Exception(f"Error ranking projects: {str(e)}")
