# Testing Team - Claude Code Skills

This directory contains specialized testing roles for the Desaka project. Each senior tester has 3-5 junior team members and specific areas of expertise.

## Team Structure

### 🧪 Testing Specialists

1. **Senior Penetration Tester** (`senior-penetration-tester.md`)
   - Expertise: Web app penetration testing, OWASP Top 10, exploit testing
   - Juniors: 3 Junior Penetration Testers + 2 Junior Security Analysts

2. **Senior Unit Test Specialist** (`senior-unit-test-specialist.md`)
   - Expertise: Unit testing, TDD, mocking, test coverage
   - Juniors: 4 Junior Unit Test Engineers + 2 Junior Test Automation Developers

3. **Senior Integration Test Specialist** (`senior-integration-test-specialist.md`)
   - Expertise: Integration testing, API testing, database integration
   - Juniors: 4 Junior Integration Test Engineers + 2 Junior QA Automation Engineers

4. **Senior Performance Test Specialist** (`senior-performance-test-specialist.md`)
   - Expertise: Performance profiling, bottleneck identification, optimization
   - Juniors: 4 Junior Performance Test Engineers + 2 Junior Load Test Engineers

5. **Senior End-to-End Test Specialist** (`senior-e2e-test-specialist.md`)
   - Expertise: E2E workflow testing, user acceptance testing, browser automation
   - Juniors: 4 Junior E2E Test Engineers + 3 Junior QA Automation Engineers

6. **Senior Load Test Specialist** (`senior-load-test-specialist.md`)
   - Expertise: Load testing, stress testing, scalability testing
   - Juniors: 3 Junior Load Test Engineers + 2 Junior Stress Test Analysts

7. **Senior Regression Test Specialist** (`senior-regression-test-specialist.md`)
   - Expertise: Regression test suites, baseline testing, automated regression
   - Juniors: 4 Junior Regression Test Engineers + 2 Junior QA Analysts

8. **Senior Security Test Specialist** (`senior-security-test-specialist.md`)
   - Expertise: SAST, DAST, dependency scanning, secrets detection
   - Juniors: 3 Junior Security Test Engineers + 2 Junior Compliance Testers

## Testing Coverage Matrix

| Test Type | Responsible Team | Coverage Target |
|-----------|-----------------|-----------------|
| Unit Tests | Unit Test Specialist | 95% code coverage |
| Integration Tests | Integration Test Specialist | All module interfaces |
| E2E Tests | E2E Test Specialist | All user workflows |
| Performance Tests | Performance Test Specialist | All critical paths |
| Load Tests | Load Test Specialist | Breaking point identification |
| Security Tests | Penetration + Security Test | OWASP Top 10 + compliance |
| Regression Tests | Regression Test Specialist | All existing functionality |

## How to Use

Each skill can be invoked using the `/skill` command in Claude Code:

```bash
# Example: Run penetration testing
/senior-penetration-tester "Test the Nittaku downloader for security vulnerabilities"

# Example: Run unit testing
/senior-unit-test-specialist "Write unit tests for parser.py with 95% coverage"

# Example: Run E2E testing
/senior-e2e-test-specialist "Test the complete download → unify → export workflow"
```

## Behavioral Protocol

All testers follow this hierarchy:

**User (Customer)**
  ↓ (humble, request feedback)
**Senior Testers**
  ↓ (mentor, praise/criticize)
**Junior Testers**

### Senior → User
- **Success**: Report results professionally
- **Failure**: Apologize and request criticism for improvement

### Senior → Junior
- **Good work**: Praise specifically
- **Poor work**: Criticize constructively with guidance

## Integration with CI/CD

Testing is integrated at multiple stages:

1. **Pre-commit**: Unit + Security tests
2. **PR Review**: Integration + Regression tests
3. **Staging**: E2E + Performance tests
4. **Production**: Load + Penetration tests (scheduled)

---

**Remember**: Quality is everyone's responsibility. Test early, test often, test thoroughly.