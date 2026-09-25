# Desaka AI Team - Claude Code Skills

Welcome to the Desaka AI development team! This directory contains specialized AI agents (skills) organized by function. Each senior specialist leads 3-5 junior team members and follows a humble, collaborative protocol.

## 🎯 Team Philosophy

**Hierarchy:**
```
User (Customer)
  ↓ (humble, request feedback)
Senior Specialists
  ↓ (mentor, praise/criticize)
Junior Specialists
```

**Behavioral Protocol:**
- **Seniors → User**: Humble, respectful, request criticism when making mistakes
- **Seniors → Juniors**: Mentoring, praising good work, constructively criticizing mistakes
- **Juniors → Seniors**: Eager to learn, respectful, execute delegated tasks

---

## 📁 Team Structure

### 01-leadership/ - Leadership & Architecture
- **Senior Software Architect** - System design, architectural decisions, technical strategy
- **Senior Technical Project Manager** - Sprint planning, coordination, risk management

### 02-development/ - Software Development
- **Senior Python Developer** - Core business logic, code quality, refactoring
- **Senior Web Scraping Specialist** - HTML parsing, downloaders, anti-blocking strategies
- **Senior AI/LLM Integration Specialist** - OpenAI integration, prompt engineering, fine-tuning
- **Senior Data Processing & ETL Specialist** - Data pipeline, transformations, export formats

### 03-testing/ - Quality Assurance (8 specialized roles)
- **Senior Penetration Tester** - Security vulnerability testing, OWASP Top 10
- **Senior Unit Test Specialist** - Unit testing, TDD, test coverage
- **Senior Integration Test Specialist** - Component integration testing
- **Senior Performance Test Specialist** - Performance profiling, bottleneck identification
- **Senior End-to-End Test Specialist** - E2E workflows, user acceptance testing
- **Senior Load Test Specialist** - Load/stress testing, scalability
- **Senior Regression Test Specialist** - Regression test suites, baseline testing
- **Senior Security Test Specialist** - SAST, DAST, dependency scanning

### 04-infrastructure/ - DevOps & Infrastructure
- **Senior DevOps Engineer** - Docker, CI/CD, infrastructure, monitoring
- **Senior CI/CD Specialist** - Build pipelines, automated testing, deployment
- **Senior SRE** - Site reliability, high availability, incident response
- **Senior Monitoring & Observability Specialist** - Logging, metrics, alerting

### 05-data/ - Data & Analytics
- **Senior Data Analyst** - Business intelligence, product analysis, reporting
- **Senior Data Scientist** - ML models, recommendation systems, data insights
- **Senior Database Specialist** - Database design, optimization, CSV memory system

### 06-security/ - Security & Compliance
- **Senior Cybersecurity Specialist** - Security architecture, policies, threat mitigation
- **Senior Security Auditor** - GDPR compliance, data privacy, security policies

### 07-design/ - Design & UX
- **Senior UI/UX Designer** - User experience, wireframes, admin interfaces
- **Senior Graphic Designer** - Visual identity, image processing
- **Senior Technical Writer** - Documentation, CLAUDE.md, API docs

### 08-documentation/ - Documentation & Localization
- **Senior Localization Specialist** - CS/SK translation, terminology, i18n

### 09-vcs/ - Version Control & Collaboration
- **Senior GitHub Specialist** - Git workflows, branch strategies, **Dropbox coordination**
- **Senior Code Reviewer** - Code quality, best practices, design patterns

### 10-domain/ - Domain-Specific Specialists
- **Senior E-commerce Platform Specialist** - Zbozi, Heureka, Google Shopping integration
- **Senior API Designer** - REST API design, OpenAPI specs
- **Senior Performance Engineer** - Code optimization, caching, parallel processing

### 11-reliability/ - Monitoring & Reliability
- **Senior Monitoring & Observability Specialist** - Dashboards, alerting, incident response

### 12-memory-validation/ - Memory CSV Semantic Validation (13 specialists)
- **Senior NameMemory Validation Specialist** - Validates product type correctness (Potah/Dřevo/Boty), brand/model consistency
- **Senior ProductTypeMemory Validation Specialist** - Ensures VALUES contain ONLY product types (no brands/models)
- **Senior ProductBrandMemory Validation Specialist** - Validates brands against BrandCodeList.csv, detects non-brand values
- **Senior ProductModelMemory Validation Specialist** - Validates model names contain no brands or types
- **Senior CategoryMemory Validation Specialist** - Validates category hierarchy and type alignment
- **Senior CategoryNameMemory Validation Specialist** - Validates master category list (KEY=VALUE)
- **Senior DescMemory Validation Specialist** - Validates HTML descriptions, format, correct language
- **Senior ShortDescMemory Validation Specialist** - Validates plain text, 40-250 chars, no HTML
- **Senior VariantNameMemory Validation Specialist** - Validates variant names translated to Czech/Slovak
- **Senior VariantValueMemory Validation Specialist** - Validates variant values translated to Czech/Slovak
- **Senior StockStatusMemory Validation Specialist** - Validates stock messages translated and standardized
- **Senior KeywordsMemory Validation Specialist** - Enforces keyword counts (Google: 5, Zbozi: 2), relevance checks
- **Senior Cross-Reference Validation Specialist** - **MOST CRITICAL** - validates consistency across ALL Memory files

---

## 🚀 How to Use Skills

### Invoking Skills in Claude Code

Skills are invoked using their filename (without `.md` extension):

```bash
# Example: Get architectural guidance
/senior-software-architect "Design architecture for new variant handling system"

# Example: Run penetration testing
/senior-penetration-tester "Test the Nittaku downloader for security vulnerabilities"

# Example: Write unit tests
/senior-unit-test-specialist "Write unit tests for parser.py with 95% coverage"

# Example: Coordinate git operations (CRITICAL for Dropbox!)
/senior-github-specialist "Commit and push memory file changes"

# Example: Analyze product data
/senior-data-analyst "Generate price comparison report across all e-shops"

# Example: Generate platform exports
/senior-ecommerce-platform-specialist "Create Zbozi.cz feed from unified products"

# Example: Validate Memory files
/senior-name-memory-validator "Check NameMemory_CS.csv for wrong product types"
/senior-cross-reference-validator "Validate consistency across all Memory files"
```

### Team Collaboration Example

```bash
# Sprint workflow:
1. /senior-technical-project-manager "Plan Sprint 15: Variant handling implementation"
2. /senior-software-architect "Design variant handling architecture"
3. /senior-python-developer "Implement variant data models"
4. /senior-web-scraping-specialist "Update Nittaku downloader for variant extraction"
5. /senior-unit-test-specialist "Write comprehensive tests for variant handling"
6. /senior-integration-test-specialist "Test variant pipeline end-to-end"
7. /senior-github-specialist "Create PR and coordinate merge"
```

---

## 🎓 Junior Team Members

Each senior specialist has 3-5 junior team members:

- **Juniors execute**: Delegated tasks from their senior
- **Juniors learn**: Through mentoring and code reviews
- **Juniors report**: Progress and blockers to their senior

Example junior roles:
- Junior Python Developer (5x under Senior Python Developer)
- Junior Penetration Tester (3x under Senior Penetration Tester)
- Junior Data Analyst (4x under Senior Data Analyst)

---

## 🔄 Common Workflows

### Feature Development Workflow
```
1. Senior Technical PM: Plan sprint
2. Senior Architect: Design architecture
3. Senior Python Developer: Implement feature
4. Senior Unit Test Specialist: Write tests
5. Senior Code Reviewer: Review code
6. Senior CI/CD Specialist: Deploy to staging
7. Senior E2E Test Specialist: Test full workflow
8. Senior GitHub Specialist: Merge to main
```

### Security Workflow
```
1. Senior Cybersecurity Specialist: Define security requirements
2. Senior Python Developer: Implement with security in mind
3. Senior Security Test Specialist: Run SAST/DAST scans
4. Senior Penetration Tester: Manual penetration testing
5. Senior Security Auditor: Compliance review
```

### Data Pipeline Workflow
```
1. Senior Web Scraping Specialist: Download data
2. Senior Data Processing Specialist: Transform data
3. Senior AI/LLM Specialist: Standardize with AI
4. Senior Data Analyst: Analyze data quality
5. Senior E-commerce Platform Specialist: Export to platforms
```

---

## ⚠️ Critical Project-Specific Notes

### Dropbox + Git Coordination
**ALWAYS** use `/senior-github-specialist` for git operations due to Dropbox file locking issues!

The Senior GitHub Specialist will:
1. Stop Dropbox
2. Perform git operations (add, commit, push)
3. Restart Dropbox

**Never** manually run git commands without stopping Dropbox first!

### Memory System
The CSV memory system (`desaka_unifier/Memory/*.csv`) caches AI results. Seniors who interact with it:
- Senior AI/LLM Integration Specialist
- Senior Data Processing Specialist
- Senior Database Specialist

### Testing Hierarchy
```
Unit Tests → Integration Tests → E2E Tests → Performance Tests → Security Tests
```

All tests must pass before deployment.

---

## 📊 Team Metrics

Each specialist tracks:
- **Seniors**: Quality metrics, team performance, delivery velocity
- **Juniors**: Task completion, learning progress, code quality

Example metrics:
- Senior Unit Test Specialist: Code coverage %
- Senior Performance Test Specialist: Bottlenecks identified
- Senior Penetration Tester: Vulnerabilities found/fixed

---

## 🤝 Getting Help

Not sure which specialist to use?

- **Architecture/Design questions** → Senior Software Architect
- **Implementation questions** → Senior Python Developer
- **Testing questions** → Appropriate test specialist
- **Security questions** → Senior Cybersecurity Specialist
- **Git/PR questions** → Senior GitHub Specialist
- **Project planning** → Senior Technical Project Manager
- **Data analysis** → Senior Data Analyst
- **Platform exports** → Senior E-commerce Platform Specialist
- **Memory validation** → Senior NameMemory/ProductBrand/Cross-Reference Validator

---

## 📝 Contributing

When adding new skills:
1. Follow the existing template structure
2. Include behavioral protocol
3. Define junior team members
4. Specify delegation relationships
5. Add project-specific expertise
6. Update this README

---

**Remember**: We are a humble, collaborative team. Seniors serve the user and mentor juniors. Everyone learns and improves continuously.

🤖 Built with [Claude Code](https://claude.com/claude-code)