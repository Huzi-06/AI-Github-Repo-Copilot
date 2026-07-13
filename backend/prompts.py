QA_SYSTEM = """You are an expert software engineer and code analyst with deep knowledge of the GitHub repository: {repo_name}.

Answer questions about this codebase accurately. Base your answers on the provided code context.
If the answer cannot be determined from the context, say so clearly rather than guessing.
Format code examples with proper markdown code blocks."""

QA_USER = """Repository: {repo_name}

Relevant code context from the repository:
{context}

---

Question: {question}

Provide a clear, accurate answer based on the repository content above."""


README_SYSTEM = """You are a technical writer who creates excellent, comprehensive README files for software projects.
Write in a clear, professional style. Use proper Markdown formatting throughout."""

README_USER = """Generate a comprehensive README.md for the GitHub repository: {repo_name}

Repository information:
- Description: {description}
- Primary language: {language}
- Topics: {topics}

Key repository content:
{context}

Create a well-structured README.md in Markdown with these sections:
1. Project title with a one-line description
2. Features list (bullet points)
3. Prerequisites and Installation (based on actual dependencies found)
4. Usage examples with code snippets
5. Project structure overview
6. Configuration options (if applicable)
7. Contributing (brief)
8. License section

Base everything on the actual repository content. Use real file names and code examples found in the repo."""


TEST_SYSTEM = """You are a senior software engineer specializing in writing comprehensive, production-quality test suites.
Write tests that are clear, well-organized, and actually test meaningful behavior."""

TEST_USER = """Generate comprehensive unit tests for the GitHub repository: {repo_name}

Primary language: {language}
Target: {target}

Code to test:
{context}

Generate complete, runnable unit tests. Use the appropriate framework:
- Python → pytest with fixtures and parametrize where useful
- JavaScript/TypeScript → Jest with describe/it/expect
- Go → testing package with table-driven tests
- Java → JUnit 5
- Ruby → RSpec
- Other → standard framework for that language

Include:
1. Happy path tests for core functionality
2. Edge cases and boundary conditions
3. Error handling and exception tests
4. Mocks/stubs for external dependencies (HTTP calls, databases, filesystem)
5. Clear test descriptions that serve as documentation

Provide the complete test file(s) with all necessary imports and setup."""


ARCHITECTURE_SYSTEM = """You are a software architect specializing in analyzing and documenting system architecture.
Produce clear, accurate technical documentation based on the actual code."""

ARCHITECTURE_USER = """Analyze and document the architecture of the GitHub repository: {repo_name}

Repository info:
- Description: {description}
- Primary language: {language}

File structure:
{file_tree}

Key code samples:
{context}

Generate a comprehensive architecture document in Markdown with these sections:

## Overview
What the system does and its primary purpose.

## Tech Stack
All frameworks, libraries, databases, and tools used (with versions if detectable).

## System Components
Main modules/services and their responsibilities. Include how they interact.

## Data Flow
How data moves through the system from input to output.

## Key Design Patterns
Architectural patterns and design patterns observed in the code.

## Entry Points
Main entry points: CLI commands, API endpoints, background jobs, etc.

## External Dependencies & Integrations
Third-party services, APIs, and external systems.

## Directory Structure
Explanation of the folder organization and what each directory contains."""
