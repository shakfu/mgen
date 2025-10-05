# Security Policy

## Supported Versions

MGen is currently in beta (v0.1.x). Security updates are provided for the latest release only.

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue in MGen, please report it responsibly:

### How to Report

**DO NOT** create a public GitHub issue for security vulnerabilities.

Instead, please email security reports to: [Your security contact email]

Or use GitHub's private vulnerability reporting: https://github.com/[your-org]/mgen/security/advisories/new

### What to Include

Please include the following information in your report:

- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- Any suggested fixes (if applicable)
- Your contact information for follow-up

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Varies by severity (critical issues within 2 weeks)

We will keep you informed throughout the process and credit you in the security advisory (unless you prefer to remain anonymous).

## Security Considerations

### Code Generation Safety

MGen generates code from Python source. Users should be aware of the following:

#### Input Validation

- **Untrusted Code**: Do not run MGen on untrusted Python source code without review
- **Generated Code**: Always review generated code before use in production
- **Subprocess Usage**: MGen uses subprocess for compilation and execution during testing
  - Build commands are validated and use specific executable paths
  - No shell=True usage for subprocess calls
  - Argument lists are explicitly constructed (no string interpolation)

#### Subprocess Security

MGen's build system (`src/mgen/backends/*/builder.py`) uses subprocess for:

1. **Compilation** - Calling language-specific compilers (gcc, rustc, ghc, etc.)
   - Executable paths are hardcoded or from environment
   - Arguments are list-based (not shell strings)
   - Working directory is controlled

2. **Execution** - Running generated binaries for testing
   - Binary paths are explicit
   - Timeouts are enforced
   - No untrusted input to subprocess

**Best Practices**:
- Only use MGen on code you trust
- Review generated code before production use
- Run MGen in isolated environments for untrusted inputs
- Keep MGen updated to receive security patches

### Cryptographic Hashing

- MGen uses SHA-256 for cache key generation (non-cryptographic purpose)
- No sensitive data is hashed or stored

### Dependencies

- **Zero Runtime Dependencies**: Generated code has no external dependencies
- **Development Dependencies**: Listed in `pyproject.toml`
  - Regularly updated via `uv` package manager
  - Security advisories monitored

### Data Privacy

- MGen does not collect, transmit, or store user data
- All code generation happens locally
- No telemetry or analytics

## Security Best Practices for Users

### Code Review

1. **Review Generated Code**: Always inspect generated code before deployment
2. **Test Thoroughly**: Run comprehensive tests on generated code
3. **Static Analysis**: Use language-specific linters on output

### Isolation

1. **Containerization**: Consider running MGen in containers for untrusted input
2. **Permission Limits**: Run with minimal necessary permissions
3. **Network Isolation**: No network access required for code generation

### Updates

1. **Stay Current**: Update to latest version for security fixes
2. **Monitor Releases**: Watch the repository for security advisories
3. **Review Changelogs**: Check CHANGELOG.md for security-related changes

## Known Security Limitations

### Non-Goals

MGen is **not** designed for:

- Running untrusted code in production without review
- Automatic security hardening of generated code
- Sandboxed execution of arbitrary Python code

### Scope

Security guarantees apply to:

- Code generation process (no code injection)
- Build system safety (validated subprocess usage)
- Generated code correctness (not security hardening)

## Security Updates

Security fixes are documented in:

- `CHANGELOG.md` - Under "Security" section
- GitHub Security Advisories
- Release notes

## Acknowledgments

We appreciate security researchers who responsibly disclose vulnerabilities. Contributors will be credited in:

- Security advisories
- CHANGELOG.md
- GitHub repository acknowledgments

## Contact

For security concerns: [Your security contact email]

For general questions: https://github.com/[your-org]/mgen/issues

---

Last updated: 2025-10-05
