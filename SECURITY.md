# Security Policy

## Supported Versions

We actively support the following versions of FinOps Agent with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of FinOps Agent seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### How to Report

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: [security@finopsagent.org] (replace with actual email)

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

### What to Include

Please include the following information in your report:

- Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit the issue

### Response Process

1. **Acknowledgment**: We will acknowledge receipt of your vulnerability report within 48 hours
2. **Investigation**: We will investigate and validate the reported vulnerability
3. **Resolution**: We will work on a fix and coordinate the release timeline with you
4. **Disclosure**: We will publicly disclose the vulnerability after a fix is available

### Security Best Practices

When deploying FinOps Agent, please follow these security best practices:

- Use environment variables for all sensitive configuration
- Enable AWS CloudTrail for audit logging
- Use IAM roles with least-privilege access
- Keep all dependencies up to date
- Use HTTPS/TLS for all communications
- Regularly review and rotate access credentials

## Security Features

FinOps Agent includes several built-in security features:

- **No Hardcoded Credentials**: All sensitive data is externalized
- **IAM Integration**: Uses AWS IAM for authentication and authorization
- **Encrypted Communication**: All API calls use HTTPS/TLS
- **Input Validation**: Comprehensive input validation and sanitization
- **Audit Logging**: Comprehensive logging for security monitoring

Thank you for helping keep FinOps Agent and our users safe!
