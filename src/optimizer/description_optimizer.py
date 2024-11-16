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
                model="gpt-3.5-turbo",
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
            output_dir = Path(f'output/{timestamp}_{position_name}')
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

    def _optimize_single_project(
        self,
        rank_info: Dict,
        original_projects: List[Dict],
        relevant_skills: Dict
    ) -> Optional[Dict]:
        """Optimize a single project description while maintaining authenticity."""
        project_title = rank_info.get('id')
        if not project_title:
            print(f"{Fore.YELLOW}Warning: Missing project title in ranking info{Style.RESET_ALL}")
            return None
        
        matching_projects = [p for p in original_projects if p.get('title') == project_title]
        if not matching_projects:
            print(f"{Fore.YELLOW}Warning: No matching project found for title: {project_title}{Style.RESET_ALL}")
            return None
            
        original_project = matching_projects[0]
        original_description = original_project.get('description', '')
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{
                    "role": "system",
                    "content": "You are a technical resume optimizer that makes subtle but effective improvements to project descriptions."
                },
                {
                    "role": "user",
                    "content": f"""
                    Original description: {original_description}
                    
                    Job context and relevant skills:
                    {json.dumps(relevant_skills, indent=2)}
                    
                    Modify this description to:
                    1. Highlight relevant technical aspects
                    2. Use industry-standard terminology
                    3. Keep the same achievements and metrics
                    4. Stay within 50% of original length
                    5. Focus on the most relevant skills for this job
                    
                    Return ONLY the modified description, no explanations.
                    """
                }],
                temperature=0.5,
            )
            
            optimized_description = response.choices[0].message.content.strip()
            
            # Print the attempted modification for debugging
            print(f"\n{Fore.CYAN}Project: {project_title}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Original:{Style.RESET_ALL} {original_description}")
            print(f"{Fore.YELLOW}Attempted:{Style.RESET_ALL} {optimized_description}")
            
            # Validate changes
            if len(optimized_description.split()) > len(original_description.split()) * 1.5:
                print(f"{Fore.RED}Changes too extensive, using original{Style.RESET_ALL}")
                optimized_description = original_description
            
            return {
                **original_project,
                'title': project_title,
                'description': optimized_description,
                'original_description': original_description,
                'relevance_score': rank_info.get('relevance_score', 0),
                'optimization_reason': rank_info.get('reason', '')
            }
            
        except Exception as e:
            print(f"{Fore.RED}Error in API call for project {project_title}: {str(e)}{Style.RESET_ALL}")
            return None

    def _validate_changes(self, original: str, optimized: str, relevant_skills: Dict) -> bool:
        """Validate that the changes made are reasonable and maintain authenticity."""
        # Calculate word-level changes
        original_words = set(original.lower().split())
        optimized_words = set(optimized.lower().split())
        
        # Calculate change percentage
        changed_words = len(original_words.symmetric_difference(optimized_words))
        total_words = len(original_words)
        change_percentage = (changed_words / total_words) * 100
        
        print(f"\n{Fore.CYAN}Change Analysis:{Style.RESET_ALL}")
        print(f"Words changed: {changed_words}/{total_words} ({change_percentage:.1f}%)")
        
        # More permissive validation
        if change_percentage > 50:
            print(f"{Fore.RED}Too many words changed ({change_percentage:.1f}%){Style.RESET_ALL}")
            return False
            
        # Check length ratio
        length_ratio = len(optimized) / len(original)
        if length_ratio < 0.8 or length_ratio > 1.5:
            print(f"{Fore.RED}Length ratio out of bounds: {length_ratio:.2f}{Style.RESET_ALL}")
            return False
        
        return True

    def _create_optimization_prompt(self, project: Dict, relevant_skills: Dict) -> str:
        """Create a prompt for more focused optimization."""
        return f"""
        Optimize this project description for a job application:
        "{project.get('description', '')}"
        
        Requirements:
        1. Keep the same technical achievements and metrics
        2. Highlight these relevant skills: {', '.join(relevant_skills.get('technical_skills', []))}
        3. Use appropriate terminology from: {', '.join(relevant_skills.get('domain_knowledge', []))}
        4. Maintain similar length and structure
        5. Focus on emphasizing relevant experience without adding new claims
        
        Example of good optimization:
        Original: "Built a control system using Python"
        Good: "Developed control system software in Python, implementing feedback loops for system monitoring"
        
        Return ONLY the optimized description.
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
