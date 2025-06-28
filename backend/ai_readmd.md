# AI Development Guidelines

## Core Principles

1. **Understand Before Acting**: Do NOT rewrite code immediately upon finding an error
2. **Structure First**: Always analyze the current project structure first
3. **Root Cause Analysis**: Find out WHY something is wrong before fixing
4. **Major Changes Require Approval**: If extensive rewriting is needed, ask for permission first
5. **Preserve Core Functions**: Rewriting risks missing essential functionality
6. **Documentation Review**: Read ALL api.md files to understand the complete system

## Development Workflow

### Step 1: Complete Documentation Review
- Read all API documentation files (api_*.md)
- Understand the current project structure
- Map existing implementations vs. planned features
- Identify what's working vs. what needs implementation

### Step 2: Error Analysis
- When encountering errors, investigate the root cause
- Check imports, dependencies, and file structures
- Understand the relationship between files
- Avoid immediate rewrites

### Step 3: Minimal Fixes
- Make targeted fixes rather than complete rewrites
- Preserve existing working functionality
- Only modify what's absolutely necessary

### Step 4: Major Changes Protocol
- If extensive changes are needed, explain the situation first
- Get approval before major rewrites
- Explain what core functions might be affected
- Propose alternative solutions if possible

## Current Understanding
The project is a Campus LLM system with:
- Authentication system (completed)
- Semester/Course management (partially implemented)
- File management (planned)
- Chat/RAG system (planned)
- Admin functions (planned)

I acknowledge that rushing to rewrite code can lose important existing functionality and will follow these guidelines going forward.