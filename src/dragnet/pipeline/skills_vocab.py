"""Curated skills vocabulary. Matching and canonicalization live in `skills.py`.

One row per canonical skill: (name, category, aliases). Aliases are matched
case-insensitively as whole tokens. Keep aliases specific: a bare "go", "r", "c"
or "arm" hits ordinary English, so those get context phrases instead.
"""

from __future__ import annotations

from typing import NamedTuple


class Skill(NamedTuple):
    name: str
    category: str
    aliases: tuple[str, ...]


VOCAB: tuple[Skill, ...] = (
    # languages
    Skill("Python", "language", ("python", "python3")),
    Skill("Java", "language", ("java",)),
    Skill("C", "language", ("c/c++", "embedded c", "c programming", "c language", "ansi c")),
    Skill("C++", "language", ("c++", "cpp")),
    Skill("C#", "language", ("c#", "csharp")),
    Skill("Go", "language", ("golang", "go lang")),
    Skill("Rust", "language", ("rust",)),
    Skill("TypeScript", "language", ("typescript",)),
    Skill("JavaScript", "language", ("javascript", "es6")),
    Skill("Swift", "language", ("swift", "swiftui")),
    Skill("Kotlin", "language", ("kotlin",)),
    Skill("SQL", "language", ("sql",)),
    Skill("Bash", "language", ("bash", "shell scripting")),
    Skill("Scala", "language", ("scala",)),
    Skill("R", "language", ("r programming", "r language", "r/python", "python/r")),
    Skill("MATLAB", "language", ("matlab", "simulink")),
    Skill("Verilog", "language", ("verilog", "systemverilog", "vhdl")),
    # frameworks and libraries
    Skill("React", "framework", ("react", "react.js", "reactjs", "react native")),
    Skill("Node.js", "framework", ("node.js", "nodejs", "node js")),
    Skill("Django", "framework", ("django",)),
    Skill("Flask", "framework", ("flask",)),
    Skill("FastAPI", "framework", ("fastapi",)),
    Skill("Spring", "framework", ("spring boot", "spring framework")),
    Skill(".NET", "framework", (".net", "dotnet", "asp.net")),
    Skill("PyTorch", "ml", ("pytorch", "torch")),
    Skill("TensorFlow", "ml", ("tensorflow", "keras")),
    Skill("scikit-learn", "ml", ("scikit-learn", "sklearn", "scikit learn")),
    Skill("pandas", "data", ("pandas",)),
    Skill("NumPy", "data", ("numpy",)),
    Skill("Spark", "data", ("spark", "pyspark", "apache spark")),
    Skill("Kafka", "data", ("kafka",)),
    Skill("Airflow", "data", ("airflow",)),
    Skill("Hadoop", "data", ("hadoop",)),
    # cloud and infrastructure
    Skill("AWS", "cloud", ("aws", "amazon web services")),
    Skill("Azure", "cloud", ("azure",)),
    Skill("GCP", "cloud", ("gcp", "google cloud")),
    Skill("Docker", "devops", ("docker", "containers", "containerization")),
    Skill("Kubernetes", "devops", ("kubernetes", "k8s")),
    Skill("Terraform", "devops", ("terraform",)),
    Skill("Ansible", "devops", ("ansible",)),
    Skill("Jenkins", "devops", ("jenkins",)),
    Skill("GitHub Actions", "devops", ("github actions",)),
    Skill("CI/CD", "devops", ("ci/cd", "cicd", "continuous integration", "continuous delivery")),
    Skill("Git", "devops", ("git", "github", "gitlab", "version control")),
    Skill("Linux", "devops", ("linux", "unix")),
    # databases
    Skill("PostgreSQL", "database", ("postgresql", "postgres")),
    Skill("MySQL", "database", ("mysql",)),
    Skill("MongoDB", "database", ("mongodb", "mongo")),
    Skill("Redis", "database", ("redis",)),
    Skill("SQLite", "database", ("sqlite",)),
    Skill("Elasticsearch", "database", ("elasticsearch", "opensearch")),
    Skill("Snowflake", "database", ("snowflake",)),
    # embedded
    Skill("RTOS", "embedded", ("rtos", "freertos", "zephyr", "real-time operating system")),
    Skill("FPGA", "embedded", ("fpga", "fpgas")),
    Skill("ARM", "embedded", ("arm cortex", "cortex-m", "arm architecture", "arm processor")),
    Skill("Microcontrollers", "embedded", ("microcontroller", "microcontrollers", "mcu", "stm32")),
    Skill("Serial buses", "embedded", ("i2c", "spi", "uart", "can bus")),
    Skill("ROS", "embedded", ("ros", "ros2", "robot operating system")),
    # concepts and tooling
    Skill("REST APIs", "concept", ("rest", "rest api", "restful", "rest apis")),
    Skill("GraphQL", "concept", ("graphql",)),
    Skill("Microservices", "concept", ("microservices", "microservice")),
    Skill("Machine learning", "ml", ("machine learning", "ml")),
    Skill("Deep learning", "ml", ("deep learning", "neural networks")),
    Skill("NLP", "ml", ("nlp", "natural language processing")),
    Skill("Computer vision", "ml", ("computer vision", "opencv")),
    Skill("LLMs", "ml", ("llm", "llms", "large language models", "generative ai", "genai")),
    Skill("Data structures", "concept", ("data structures", "algorithms")),
    Skill("Agile", "process", ("agile", "scrum", "kanban")),
    Skill("Testing", "process", ("unit testing", "unit tests", "pytest", "junit", "test-driven")),
    Skill("Excel", "tooling", ("excel", "spreadsheets")),
    Skill("Tableau", "tooling", ("tableau", "power bi", "looker")),
    Skill("Jira", "tooling", ("jira",)),
)
