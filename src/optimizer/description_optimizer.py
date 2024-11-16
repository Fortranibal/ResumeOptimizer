# src/optimizer/description_optimizer.py

from openai import OpenAI
from typing import Dict, List

class DescriptionOptimizer:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def optimize_descriptions(
        self, 
        original_projects: List[Dict], 
        relevant_skills: Dict, 
        ranked_projects: List[Dict]
    ) -> List[Dict]:
        """
        Optimize project descriptions to better match job requirements while maintaining authenticity.
        
        Args:
            original_projects: List of original project descriptions
            relevant_skills: Dictionary of skills extracted from job description
            ranked_projects: List of ranked projects by relevance
            
        Returns:
            List of projects with optimized descriptions
        """
        optimized_projects = []
        
        for project in ranked_projects[:3]:  # Focus on top 3 most relevant projects
            project_id = project['id']
            original_project = next(p for p in original_projects if p['id'] == project_id)
            
            # Extract skills to emphasize
            technical_skills = ', '.join(relevant_skills.get('technical_skills', []))
            domain_knowledge = ', '.join(relevant_skills.get('domain_knowledge', []))
            technologies = ', '.join(relevant_skills.get('technologies', []))
            
            prompt = f"""
            Original project description: {original_project['description']}
            
            Considering these elements from the job requirements:
            Technical skills: {technical_skills}
            Domain knowledge: {domain_knowledge}
            Technologies: {technologies}
            
            Rewrite the project description to:
            1. Naturally incorporate more relevant keywords and terms
            2. Maintain the same basic structure and length
            3. Keep the core message and achievements intact
            4. Make only minimal, strategic changes
            5. Ensure the text remains authentic and believable
            
            Return only the modified description text.
            """
            
            try:
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.5,  # Lower temperature for more consistent output
                )
                
                optimized_description = response.choices[0].message.content.strip()
                
                optimized_projects.append({
                    **original_project,
                    'description': optimized_description,
                    'original_description': original_project['description'],
                    'relevance_score': project.get('relevance_score', 0),
                    'optimization_reason': project.get('reason', '')
                })
                
            except Exception as e:
                print(f"Error optimizing project {project_id}: {str(e)}")
                optimized_projects.append(original_project)
        
        return optimized_projects
