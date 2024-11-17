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
        ranked_projects: List[Dict],
        job_description: str
    ) -> List[Dict]:
        """
        Optimize project descriptions to better match job requirements while maintaining authenticity.
        """
        optimized_projects = []
        
        try:
            # Create job-specific output directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            position_name = self._extract_position_name(job_description)
            output_dir = Path(f'output/{timestamp}_{position_name}')
            output_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"{Fore.CYAN}Creating output directory for position: {position_name}{Style.RESET_ALL}")
            
            # Debug information
            self._print_debug_info(original_projects, ranked_projects)
            
            # Process top 3 projects
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
            
            # Save results
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
        """Optimize a single project description with multiple alternatives."""
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
        
        print(f"\n{Fore.CYAN}Project: {project_title}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Original:{Style.RESET_ALL} {original_description}")
        
        try:
            # Generate three alternatives
            alternatives = []
            for i in range(1):
                response = self.client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[
                        {"role": "system", "content": "You are a technical resume optimizer that makes subtle but effective improvements to project descriptions."},
                        {"role": "user", "content": self._create_optimization_prompt(original_description, relevant_skills, i+1)}
                    ],
                    temperature=0.7 + (i * 0.1),  # Slightly increase variation for each attempt
                )
                
                alternative = response.choices[0].message.content.strip()
                print(f"\n{Fore.YELLOW}Alternative {i+1}:{Style.RESET_ALL} {alternative}")
                
                similarity_score = self._calculate_similarity_score(
                    original_description, 
                    alternative, 
                    relevant_skills
                )
                
                alternatives.append({
                    'description': alternative,
                    'similarity_score': similarity_score
                })

            # Select best alternative
            best_alternative = self._select_best_alternative(
                original_description,
                alternatives,
                relevant_skills
            )
            
            if best_alternative:
                return {
                    **original_project,
                    'title': project_title,
                    'description': best_alternative['description'],
                    'original_description': original_description,
                    'relevance_score': rank_info.get('relevance_score', 0),
                    'optimization_reason': rank_info.get('reason', ''),
                    'similarity_score': best_alternative['similarity_score']
                }
            else:
                print(f"{Fore.RED}No suitable alternative found, using original{Style.RESET_ALL}")
                return {
                    **original_project,
                    'title': project_title,
                    'description': original_description,
                    'original_description': original_description,
                    'relevance_score': rank_info.get('relevance_score', 0),
                    'optimization_reason': rank_info.get('reason', '')
                }
                
        except Exception as e:
            print(f"{Fore.RED}Error generating alternatives for {project_title}: {str(e)}{Style.RESET_ALL}")
            return None

    def _create_optimization_prompt(self, original_description: str, relevant_skills: Dict, attempt: int) -> str:
        """Create a prompt for generating alternative descriptions with technical accuracy."""
        technical_skills = ', '.join(relevant_skills.get('technical_skills', []))
        domain_knowledge = ', '.join(relevant_skills.get('domain_knowledge', []))
        technologies = ', '.join(relevant_skills.get('technologies', []))
        
        return f"""
        Original project description: {original_description}

        This is optimization attempt {attempt} of 3. Create a variation that maintains technical accuracy.
        Context: You are writing for technical recruiters who are experts in:
        - {domain_knowledge}
        - {technologies}

        Technical Requirements:
        1. NEVER modify technical metrics or performance numbers
        2. NEVER claim capabilities beyond what the mentioned tools can do
        3. Respect the actual capabilities and limitations of:
        - Each programming language mentioned
        - Each simulation tool referenced
        - Each technical framework used

        Permitted Modifications:
        1. Use industry-standard terminology for existing elements
        2. Clarify technical processes that are implicit
        3. Highlight relevant aspects without changing facts
        4. Adjust emphasis while maintaining technical truth

        Forbidden Changes:
        1. DO NOT modify performance metrics
        2. DO NOT change the core technical approach
        3. DO NOT exaggerate tool capabilities

        Example of good optimization:
        Original: "Used ANSYS for thermal simulation"
        Good: "Validated thermal system behavior using ANSYS's thermal-fluid dynamics modules"
        Bad: "Used ANSYS for real-time control" (incorrect - not its primary purpose)

        When mentioning specific tools ({technologies}):
        - Stick to their actual intended use cases
        - Use proper technical terminology
        - Respect tool limitations
        - Maintain technical credibility

        Return ONLY the optimized description. Prioritize technical accuracy over keyword matching.
        """


    def _calculate_similarity_score(
        self, 
        original: str, 
        alternative: str, 
        relevant_skills: Dict
    ) -> float:
        """Calculate similarity score between original and alternative descriptions."""
        # Calculate basic metrics
        original_words = set(original.lower().split())
        alternative_words = set(alternative.lower().split())
        
        # Word retention rate
        retained_words = len(original_words.intersection(alternative_words))
        retention_rate = retained_words / len(original_words)
        
        # Length ratio
        length_ratio = len(alternative) / len(original)
        length_penalty = 1.0 if 0.8 <= length_ratio <= 1.5 else 0.5
        
        # Keyword inclusion
        keywords = set(relevant_skills.get('technical_skills', []) + 
                      relevant_skills.get('technologies', []))
        keyword_score = sum(1 for keyword in keywords 
                           if keyword.lower() in alternative.lower()) / max(len(keywords), 1)
        
        # Calculate final score
        score = (
            (retention_rate * 0.4) +      # 40% weight on content retention
            (length_penalty * 0.3) +      # 30% weight on length
            (keyword_score * 0.3)         # 30% weight on keywords
        )
        
        print(f"{Fore.CYAN}Similarity Metrics:{Style.RESET_ALL}")
        print(f"Content Retention: {retention_rate:.2f}")
        print(f"Length Ratio: {length_ratio:.2f}")
        print(f"Keyword Score: {keyword_score:.2f}")
        print(f"Final Score: {score:.2f}")
        
        return score

    def _select_best_alternative(
        self, 
        original: str,
        alternatives: List[Dict],
        relevant_skills: Dict
    ) -> Optional[Dict]:
        """Select the best alternative based on scores and comparison."""
        print(f"\n{Fore.CYAN}Comparing Alternatives:{Style.RESET_ALL}")
        
        # Sort by similarity score
        sorted_alternatives = sorted(
            alternatives,
            key=lambda x: x['similarity_score'],
            reverse=True
        )
        
        # Print all alternatives with scores
        for i, alt in enumerate(sorted_alternatives):
            print(f"\n{Fore.YELLOW}Alternative {i+1} (Score: {alt['similarity_score']:.2f}):{Style.RESET_ALL}")
            print(alt['description'])
        
        # Select best alternative if it meets threshold
        best_alternative = sorted_alternatives[0]
        if best_alternative['similarity_score'] >= 0.7:
            print(f"\n{Fore.GREEN}Selected Best Alternative (Score: {best_alternative['similarity_score']:.2f}):{Style.RESET_ALL}")
            print(best_alternative['description'])
            return best_alternative
        
        return None

    def _save_results(
        self,
        output_dir: Path,
        optimized_projects: List[Dict],
        relevant_skills: Dict,
        ranked_projects: List[Dict]
    ) -> None:
        """Save optimization results to JSON."""
        try:
            output_file = output_dir / 'general_summary.json'
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
        """Save CV-ready descriptions with all alternatives."""
        try:
            # Save as JSON
            cv_json_file = output_dir / 'optimized_projects.json'
            cv_descriptions = {
                project['title']: {
                    'selected_description': project['description'],
                    'original_description': project['original_description'],
                    'similarity_score': project.get('similarity_score', 0),
                    'relevance_score': project.get('relevance_score', 0)
                }
                for project in optimized_projects
            }
            
            with open(cv_json_file, 'w', encoding='utf-8') as f:
                json.dump(cv_descriptions, f, indent=2, ensure_ascii=False)
            
            # Save as TXT
            cv_txt_file = output_dir / 'optimized_projects.txt'
            with open(cv_txt_file, 'w', encoding='utf-8') as f:
                for project in optimized_projects:
                    f.write(f"Project: {project['title']}\n")
                    f.write("-" * 50 + "\n")
                    f.write("Original Description:\n")
                    f.write(f"{project['original_description']}\n\n")
                    f.write("Optimized Description:\n")
                    f.write(f"{project['description']}\n")
                    if 'similarity_score' in project:
                        f.write(f"\nSimilarity Score: {project['similarity_score']:.2f}")
                    f.write(f"\nRelevance Score: {project['relevance_score']}\n")
                    f.write("\n" + "=" * 50 + "\n\n")
            
            print(f"{Fore.GREEN}CV-ready descriptions saved to:{Style.RESET_ALL}")
            print(f"{Fore.GREEN}  - {cv_json_file}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}  - {cv_txt_file}{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}Error saving CV descriptions: {str(e)}{Style.RESET_ALL}")

    def _extract_position_name(self, job_description: str) -> str:
        """
        Extract a clean position name from the job description for folder naming.
        """
        try:
            # Extract the first line which typically contains the job title
            first_line = job_description.split('\n')[0].strip()
            
            # Clean the position name for folder use
            position_name = first_line.lower()
            position_name = position_name.replace('(m/f)', '').replace('(f/m)', '')  # Remove gender indicators
            position_name = ''.join(c if c.isalnum() or c in [' ', '_', '-'] else '_' for c in position_name)
            position_name = position_name.replace(' ', '_')
            position_name = '_'.join(filter(None, position_name.split('_')))  # Remove empty parts
            
            # If the result is too long, take the first few meaningful parts
            if len(position_name) > 50:
                parts = position_name.split('_')
                position_name = '_'.join(parts[:4])  # Take first 4 parts
            
            return position_name if position_name else "job_application"
            
        except Exception as e:
            print(f"{Fore.YELLOW}Warning: Could not extract position name: {str(e)}{Style.RESET_ALL}")
            return "job_application"  # fallback name

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
