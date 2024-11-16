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

    def optimize_descriptions(
        self, 
        original_projects: List[Dict], 
        relevant_skills: Dict, 
        ranked_projects: List[Dict]
    ) -> List[Dict]:
        """
        Optimize project descriptions to better match job requirements while maintaining authenticity.
        """
        optimized_projects = []
        
        try:
            # Create job-specific output directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path(f'output/job_application_{timestamp}')
            output_dir.mkdir(parents=True, exist_ok=True)
            
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
                        optimized_projects.append(optimized_project)
                except Exception as e:
                    print(f"{Fore.RED}Error optimizing project: {str(e)}{Style.RESET_ALL}")
            
            # Save results in different formats
            self._save_results(
                output_dir,
                optimized_projects,
                relevant_skills,
                ranked_projects
            )
            
            # Generate and save CV-ready descriptions
            self._save_cv_descriptions(output_dir, optimized_projects)
            
            return optimized_projects
            
        except Exception as e:
            print(f"{Fore.RED}Debug info:{Style.RESET_ALL}")
            print(f"Ranked projects type: {type(ranked_projects)}")
            print(f"Original projects type: {type(original_projects)}")
            raise Exception(f"Optimization error: {str(e)}")

    def _optimize_single_project(
        self,
        rank_info: Dict,
        original_projects: List[Dict],
        relevant_skills: Dict
    ) -> Optional[Dict]:
        """
        Optimize a single project description.
        """
        # Extract project title (used as ID)
        project_title = rank_info.get('id')
        if not project_title:
            print(f"{Fore.YELLOW}Warning: Missing project title in ranking info{Style.RESET_ALL}")
            return None
        
        # Find matching project by title
        matching_projects = [p for p in original_projects if p.get('title') == project_title]
        if not matching_projects:
            print(f"{Fore.YELLOW}Warning: No matching project found for title: {project_title}{Style.RESET_ALL}")
            return None
            
        original_project = matching_projects[0]
        
        # Prepare optimization prompt
        prompt = self._create_optimization_prompt(original_project, relevant_skills)
        
        try:
            # Get optimized description from OpenAI
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
            )
            
            optimized_description = response.choices[0].message.content.strip()
            
            # Create optimized project dictionary
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
        Create the prompt for description optimization.
        """
        technical_skills = ', '.join(relevant_skills.get('technical_skills', []))
        domain_knowledge = ', '.join(relevant_skills.get('domain_knowledge', []))
        technologies = ', '.join(relevant_skills.get('technologies', []))
        
        return f"""
        Original project description: {project.get('description', '')}
        
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

    def _save_results(
        self,
        output_dir: Path,
        optimized_projects: List[Dict],
        relevant_skills: Dict,
        ranked_projects: List[Dict]
    ) -> None:
        """
        Save complete optimization results to JSON.
        """
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
        """
        Save CV-ready descriptions in both JSON and TXT formats.
        """
        try:
            # Save as JSON
            cv_json_file = output_dir / 'cv_descriptions.json'
            cv_descriptions = {
                project['title']: project['description']
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
                    f.write(f"{project['description']}\n")
                    f.write("\n" + "=" * 50 + "\n\n")
            
            print(f"{Fore.GREEN}CV-ready descriptions saved to:{Style.RESET_ALL}")
            print(f"{Fore.GREEN}  - {cv_json_file}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}  - {cv_txt_file}{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}Error saving CV descriptions: {str(e)}{Style.RESET_ALL}")

    def _print_debug_info(self, original_projects: List[Dict], ranked_projects: List[Dict]) -> None:
        """
        Print debug information about the projects.
        """
        try:
            if ranked_projects and original_projects:
                print(f"\n{Fore.CYAN}Ranked projects structure:{Style.RESET_ALL}")
                print(json.dumps(ranked_projects[0], indent=2))
                print(f"\n{Fore.CYAN}Original projects structure:{Style.RESET_ALL}")
                print(json.dumps(original_projects[0], indent=2))
        except Exception as e:
            print(f"{Fore.RED}Error printing debug info: {str(e)}{Style.RESET_ALL}")
