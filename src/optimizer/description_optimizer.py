# src/optimizer/description_optimizer.py

from openai import OpenAI
from typing import Dict, List, Optional
from pathlib import Path
import json
from datetime import datetime
import os
from colorama import Fore, Style

class DescriptionOptimizer:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def _extract_position_name(self, job_description: str) -> str:
        """
        Extract a clean position name from the job description for folder naming.
        """
        try:
            # Ask GPT to extract the position name
            prompt = f"""
            Extract only the job position name from this job description.
            Return ONLY the position name, nothing else.
            Make it folder-name friendly (use underscores for spaces, remove special characters).
            
            Job Description:
            {job_description[:500]}  # Using first 500 chars is usually enough for the title
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            
            position_name = response.choices[0].message.content.strip()
            
            # Clean the position name for folder use
            position_name = position_name.replace(' ', '_')
            position_name = ''.join(c for c in position_name if c.isalnum() or c in ['_', '-'])
            
            return position_name.lower()
            
        except Exception as e:
            print(f"{Fore.YELLOW}Warning: Could not extract position name: {str(e)}{Style.RESET_ALL}")
            return f"job_application"  # fallback name

    def optimize_descriptions(
        self, 
        original_projects: List[Dict], 
        relevant_skills: Dict, 
        ranked_projects: List[Dict],
        job_description: str  # Add this parameter
    ) -> List[Dict]:
        """
        Optimize project descriptions to better match job requirements while maintaining authenticity.
        """
        optimized_projects = []
        
        try:
            # Extract position name for folder
            position_name = self._extract_position_name(job_description)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path(f'output/{position_name}_{timestamp}')
            output_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"{Fore.CYAN}Creating output directory for position: {position_name}{Style.RESET_ALL}")
            
            # Debug information
            self._print_debug_info(original_projects, ranked_projects)
            
            # Process exactly top 3 projects
            for rank_info in ranked_projects[:3]:
                try:
                    optimized_project = self._optimize_single_project(
                        rank_info, 
                        original_projects, 
                        relevant_skills
                    )
                    if optimized_project:
                        # Validate changes
                        if self._validate_changes(
                            optimized_project['original_description'],
                            optimized_project['description'],
                            relevant_skills
                        ):
                            optimized_projects.append(optimized_project)
                        else:
                            # If validation fails, use original description
                            optimized_project['description'] = optimized_project['original_description']
                            optimized_projects.append(optimized_project)
                            
                except Exception as e:
                    print(f"{Fore.RED}Error optimizing project: {str(e)}{Style.RESET_ALL}")
            
            # Save results in different formats
            self._save_results(output_dir, optimized_projects, relevant_skills, ranked_projects)
            self._save_cv_descriptions(output_dir, optimized_projects)
            
            return optimized_projects
            
        except Exception as e:
            print(f"{Fore.RED}Debug info:{Style.RESET_ALL}")
            print(f"Ranked projects type: {type(ranked_projects)}")
            print(f"Original projects type: {type(original_projects)}")
            raise Exception(f"Optimization error: {str(e)}")

    def _validate_changes(self, original: str, optimized: str, relevant_skills: Dict) -> bool:
        """
        Validate that the changes made are reasonable and maintain authenticity.
        """
        # Check length difference (shouldn't change more than 20%)
        length_diff_ratio = abs(len(optimized) - len(original)) / len(original)
        if length_diff_ratio > 0.2:
            print(f"{Fore.YELLOW}Warning: Description length changed by {length_diff_ratio*100:.1f}%{Style.RESET_ALL}")
            return False

        # Check keyword density
        keywords = set(relevant_skills.get('technical_skills', []) + 
                      relevant_skills.get('technologies', []))
        
        original_keyword_count = sum(1 for keyword in keywords 
                                   if keyword.lower() in original.lower())
        optimized_keyword_count = sum(1 for keyword in keywords 
                                    if keyword.lower() in optimized.lower())
        
        if optimized_keyword_count > original_keyword_count * 1.5:
            print(f"{Fore.YELLOW}Warning: Keyword density increased too much{Style.RESET_ALL}")
            return False

        # Check sentence structure similarity (shouldn't add many new sentences)
        original_sentences = len([s for s in original.split('.') if s.strip()])
        optimized_sentences = len([s for s in optimized.split('.') if s.strip()])
        
        if abs(optimized_sentences - original_sentences) > 1:
            print(f"{Fore.YELLOW}Warning: Sentence structure changed significantly{Style.RESET_ALL}")
            return False

        return True

    def _optimize_single_project(
        self,
        rank_info: Dict,
        original_projects: List[Dict],
        relevant_skills: Dict
    ) -> Optional[Dict]:
        """
        Optimize a single project description while maintaining authenticity.
        """
        project_title = rank_info.get('id')
        if not project_title:
            print(f"{Fore.YELLOW}Warning: Missing project title in ranking info{Style.RESET_ALL}")
            return None
        
        matching_projects = [p for p in original_projects if p.get('title') == project_title]
        if not matching_projects:
            print(f"{Fore.YELLOW}Warning: No matching project found for title: {project_title}{Style.RESET_ALL}")
            return None
            
        original_project = matching_projects[0]
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{
                    "role": "user", 
                    "content": self._create_optimization_prompt(original_project, relevant_skills)
                }],
                temperature=0.3,  # Lower temperature for more conservative changes
            )
            
            optimized_description = response.choices[0].message.content.strip()
            
            return {
                **original_project,
                'title': project_title,
                'description': optimized_description,
                'original_description': original_project.get('description', ''),
                'relevance_score': rank_info.get('relevance_score', 0),
                'optimization_reason': rank_info.get('reason', '')
            }
            
        except Exception as e:
            print(f"{Fore.RED}Error in API call for project {project_title}: {str(e)}{Style.RESET_ALL}")
            return None

    def _create_optimization_prompt(self, project: Dict, relevant_skills: Dict) -> str:
        """
        Create a prompt that emphasizes minimal, authentic modifications.
        """
        technical_skills = ', '.join(relevant_skills.get('technical_skills', []))
        domain_knowledge = ', '.join(relevant_skills.get('domain_knowledge', []))
        technologies = ', '.join(relevant_skills.get('technologies', []))
        
        return f"""
        Original project description: {project.get('description', '')}
        
        Context: You are helping to subtly optimize this project description for a job application. 
        The goal is to make MINIMAL, AUTHENTIC modifications that highlight relevant experience 
        without changing the core facts or adding false claims.

        Relevant elements from job requirements:
        Technical skills: {technical_skills}
        Domain knowledge: {domain_knowledge}
        Technologies: {technologies}
        
        Instructions for modification:
        1. Keep at least 80% of the original text unchanged
        2. Only modify terms where there's a DIRECT equivalent (e.g., "created" → "developed")
        3. DO NOT add any new technical claims or achievements
        4. DO NOT add technologies or tools that weren't in the original
        5. Focus on highlighting existing relevant experience using job-appropriate terminology
        6. Maintain the original tone and level of technical detail
        7. If a skill/technology isn't explicitly mentioned in the original, DO NOT add it
        8. Keep the same quantitative metrics and achievements

        Bad example (too modified):
        Original: "Built a rocket control system using Python"
        Bad: "Engineered advanced propulsion control algorithms using Python, C++, and MATLAB for aerospace applications"
        
        Good example (subtle optimization):
        Original: "Built a rocket control system using Python"
        Good: "Developed a propulsion control system using Python"

        Return only the modified description, keeping it concise and authentic.
        If you can't make meaningful yet subtle changes, return the original description unchanged.
        """

    def _save_results(
        self,
        output_dir: Path,
        optimized_projects: List[Dict],
        relevant_skills: Dict,
        ranked_projects: List[Dict]
    ) -> None:
        """Save complete optimization results to JSON."""
        try:
            output_file = output_dir / 'optimization_results.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'optimized_projects': optimized_projects,
                    'relevant_skills': relevant_skills,
                    'ranked_projects': ranked_projects
                }, f, indent=2, ensure_ascii=False)
            print(f"{Fore.GREEN}Full results saved to: {output_file}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error saving results: {str(e)}{Style.RESET_ALL}")

    def _save_cv_descriptions(self, output_dir: Path, optimized_projects: List[Dict]) -> None:
        """Save CV-ready descriptions in both JSON and TXT formats."""
        try:
            # Save as JSON
            cv_json_file = output_dir / 'cv_descriptions.json'
            cv_descriptions = {
                project['title']: {
                    'description': project['description'],
                    'original': project['original_description'],
                    'changes_made': self._highlight_changes(
                        project['original_description'], 
                        project['description']
                    )
                }
                for project in optimized_projects
            }
            with open(cv_json_file, 'w', encoding='utf-8') as f:
                json.dump(cv_descriptions, f, indent=2, ensure_ascii=False)
            
            # Save as TXT (more CV-friendly format)
            cv_txt_file = output_dir / 'cv_descriptions.txt'
            with open(cv_txt_file, 'w', encoding='utf-8') as f:
                for project in optimized_projects:
                    f.write(f"Project: {project['title']}\n")
                    f.write("-" * 50 + "\n")
                    f.write("Original:\n")
                    f.write(f"{project['original_description']}\n\n")
                    f.write("Optimized:\n")
                    f.write(f"{project['description']}\n")
                    f.write("\n" + "=" * 50 + "\n\n")
            
            print(f"{Fore.GREEN}CV-ready descriptions saved to:{Style.RESET_ALL}")
            print(f"{Fore.GREEN}  - {cv_json_file}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}  - {cv_txt_file}{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}Error saving CV descriptions: {str(e)}{Style.RESET_ALL}")

    def _highlight_changes(self, original: str, modified: str) -> Dict[str, List[str]]:
        """Identify and list the changes made to the description."""
        return {
            "modifications": [
                f"Changed: '{orig}' → '{mod}'"
                for orig, mod in zip(original.split(), modified.split())
                if orig != mod
            ]
        }

    def _print_debug_info(self, original_projects: List[Dict], ranked_projects: List[Dict]) -> None:
        """Print debug information about the projects."""
        try:
            if ranked_projects and original_projects:
                print(f"\n{Fore.CYAN}Ranked projects structure:{Style.RESET_ALL}")
                print(json.dumps(ranked_projects[0], indent=2))
                print(f"\n{Fore.CYAN}Original projects structure:{Style.RESET_ALL}")
                print(json.dumps(original_projects[0], indent=2))
        except Exception as e:
            print(f"{Fore.RED}Error printing debug info: {str(e)}{Style.RESET_ALL}")
