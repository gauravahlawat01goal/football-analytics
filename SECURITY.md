# Security Policy

## API Key Management

This project requires a SportsMonk API key to function. Please follow these security guidelines:

### DO ✅

- Store your API key in a `.env` file (already gitignored)
- Use environment variables for sensitive credentials
- Keep your `.env` file local to your machine
- Use GitHub Secrets for automated workflows/CI-CD
- Obtain your own API key from [SportsMonk](https://www.sportmonks.com/)
- Regularly rotate your API keys
- Review `.gitignore` before committing to ensure `.env` is listed

### DON'T ❌

- Never commit your `.env` file to the repository
- Never hardcode API keys in source code
- Never share your API key publicly (social media, forums, etc.)
- Never commit files containing API keys or credentials
- Don't include API keys in code comments or documentation

## What's Protected

The following files are automatically excluded from version control (see `.gitignore`):
- `.env` - Environment variables including API keys
- `data/raw/*.csv`, `*.json` - Raw data files that might contain sensitive info
- `data/processed/*` - Processed datasets

## Reporting a Security Issue

If you discover a security vulnerability in this project:

1. **Do NOT** open a public issue
2. Email the maintainer directly (see contact info in README)
3. Include details about the vulnerability and steps to reproduce
4. Allow reasonable time for the issue to be addressed before public disclosure

## Best Practices for Contributors

If you're contributing to this project:

1. Never include real API keys in pull requests
2. Use placeholder values in example files (see `.env.example`)
3. Review your commits for accidentally included sensitive data
4. If you accidentally commit a secret, rotate it immediately and notify maintainers

## Additional Resources

- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [Twelve-Factor App: Config](https://12factor.net/config)
