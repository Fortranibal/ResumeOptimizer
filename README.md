# Resume Optimizer

A Python-based tool that optimizes project descriptions and skills for job applications using AI. This tool helps tailor your resume content to specific job descriptions by analyzing relevance and suggesting optimized descriptions.

## Features

- **Job Description Analysis**: Extracts relevant skills and requirements from job postings
- **Project Ranking**: Ranks your projects based on relevance to the job description
- **Description Optimization**: Enhances project descriptions while maintaining authenticity
- **Skills Matching**: Identifies and highlights relevant skills for the position
- **Multiple Optimization Attempts**: Generates multiple versions of optimized descriptions

## Project Structure

```bash
ResumeOptimizer/
├── src/
│   ├── optimizer/
│   │   ├── description_optimizer.py   # Handles description optimization
│   │   └── project_optimizer.py       # Manages project ranking and relevance
│   └── utils/
│       └── file_loader.py            # Handles file I/O operations
├── input/
│   ├── job_description.txt           # Target job description
│   ├── projects.json                 # Your project descriptions
│   ├── skills.json                   # Your skills database
│   └── *.tex                        # LaTeX format support files
└── LICENSE                          # MIT License
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ResumeOptimizer.git
cd ResumeOptimizer
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your OpenAI API key in `.env` file:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

1. Place your job description in `input/job_description.txt`. If already existing, update the content.
2. Add your projects to `input/projects.json`. Keep the format as shown below.
3. Define your skills in `input/skills.json`. 
4. Run the optimizer:

```bash
python main.py
```

The tool will:
- Analyze the job description
- Extract relevant skills and requirements
- Rank your projects by relevance
- Generate optimized descriptions
- Save results in the `output/` directory

## Input File Formats

### Projects (projects.json)
```json
{
  "projects": [
    {
      "title": "Project Name",
      "description": "Project description...",
      "technologies": ["Python", "OpenAI", "etc"],
      "duration": "6 months"
    }
  ]
}
```

### Skills (skills.json)
```json
{
  "technical_skills": ["Python", "Machine Learning", "etc"],
  "domain_knowledge": ["Software Development", "AI", "etc"],
  "technologies": ["Git", "Docker", "etc"]
}
```

## Features in Detail

### Description Optimizer
- Maintains authenticity while enhancing relevance
- Preserves technical details and metrics
- Generates multiple unique variations
- Ensures natural keyword incorporation

### Project Optimizer
- Ranks projects based on content relevance
- Considers keyword matches
- Evaluates description length and quality
- Provides similarity scoring

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenAI for providing the GPT API
- Contributors and maintainers
- Everyone who provides feedback and suggestions

## Author

@Fortranibal
