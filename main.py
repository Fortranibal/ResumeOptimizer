# main.py

from colorama import init, Fore, Style
import json
from datetime import datetime
from pathlib import Path
from src.utils.file_loader import FileLoader
from src.optimizer.project_optimizer import ProjectOptimizer
from src.optimizer.description_optimizer import DescriptionOptimizer

def main():
    # Initialize colorama
    init()

    print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}📝 Resume Project Optimizer Starting...{Style.RESET_ALL}")
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
        # Initialize optimizers
        project_optimizer = ProjectOptimizer(api_key)
        description_optimizer = DescriptionOptimizer(api_key)
        print(f"{Fore.GREEN}✓ Optimizers initialized{Style.RESET_ALL}")

        # Load job description
        job_description = FileLoader.load_job_description('input/job_description.txt')
        print(f"{Fore.GREEN}✓ Job description loaded successfully!{Style.RESET_ALL}")

        print(f"\n{Fore.YELLOW}🔄 Analyzing job description...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
        
        # Extract relevant skills
        print(f"\n{Fore.YELLOW}📊 Extracting relevant skills...{Style.RESET_ALL}")
        relevant_skills = project_optimizer.extract_relevant_skills(job_description)
        print(f"{Fore.GREEN}✓ Skills extracted:{Style.RESET_ALL}")
        for category, skills in relevant_skills.items():
            print(f"{Fore.CYAN}  {category}:{Style.RESET_ALL}")
            for skill in skills:
                print(f"    • {skill}")
        
        # Rank projects
        print(f"\n{Fore.YELLOW}🏆 Ranking projects...{Style.RESET_ALL}")
        ranked_projects = project_optimizer.rank_projects(job_description)
        print(f"{Fore.GREEN}✓ Projects ranked by relevance:{Style.RESET_ALL}")
        for proj in ranked_projects[:3]:
            print(f"{Fore.CYAN}  • Project {proj['id']}: {Style.RESET_ALL}")
            print(f"    Score: {proj['relevance_score']}")
            print(f"    Reason: {proj['reason']}")

        # Optimize descriptions
        print(f"\n{Fore.YELLOW}✍️ Optimizing project descriptions...{Style.RESET_ALL}")
        optimized_projects = description_optimizer.optimize_descriptions(
            project_optimizer.projects,
            relevant_skills,
            ranked_projects,
            job_description
        )
        print(f"{Fore.GREEN}✓ Descriptions optimized{Style.RESET_ALL}")

        # Save results
        output = {
            "relevant_skills": relevant_skills,
            "ranked_projects": ranked_projects,
            "optimized_projects": optimized_projects,
            "timestamp": datetime.now().isoformat()
        }
        
        output_path = Path('output/output.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"\n{Fore.GREEN}✓ Results saved to {output_path}{Style.RESET_ALL}")

    except Exception as e:
        print(f"\n{Fore.RED}✗ Error: {str(e)}{Style.RESET_ALL}")
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
