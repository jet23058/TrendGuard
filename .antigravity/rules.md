# Project Rules & Operational Standards

## 1. Security & Configuration (ZERO TOLERANCE)
**Rule: No Hardcoded Secrets.**
- **Environment Variables**: ALL sensitive data (API Keys, tokens, passwords, database URLs, client_secrets) MUST be loaded from a `.env` file.
- **Implementation**:
  - Use `os.getenv('KEY_NAME')` or `python-dotenv` for Python.
  - Never assign actual secret strings to variables in source code.
- **Git Safety**:
  - Verify that `.env` is listed in `.gitignore`.
  - Do not commit any file containing real credentials.

## 2. Testing Protocol (HIGHEST PRIORITY)
**Rule: No Code Without Tests & Verification.**
Every time you generate or modify code, you MUST follow this strict SOP:

- **1. Code & Test Generation**:
  - **New Features**: Create a corresponding unit test file (e.g., `tests/test_feature.py`) covering happy paths and edge cases.
  - **Modifications**: Update existing tests to align with logic changes.
  - **Bug Fixes**: Create a regression test that fails before the fix and passes after the fix.

- **2. Execution & Self-Verification**:
  - **Mandatory Run**: After implementing code and tests, you must execute (or simulate the execution of) the testing suite.
  - **Result Validation**: Explicitly verify that the current output results are normal and match the expected behavior.
  - **Completion Criteria**: Do not consider a task "Complete" until you have successfully generated tests, verified they pass, and confirmed the output logic is correct.

## 3. Documentation Maintenance
**Rule: Keep documentation synchronized with code.**
- **Trigger**: Post-coding phase.
- **CHANGELOG.md**:
   - Append a new entry under the current date.
   - Format: `- [Type] Description of change (File modified)`
   - Types: Feat, Fix, Refactor, Test, Docs, Security.
- **README.md**:
   - If the code change affects usage, arguments, or installation (especially new `.env` variables), update the relevant section immediately.