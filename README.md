# AI PR Reviewer

An intelligent code review system that analyzes your commits before creating pull requests. Uses AI to provide detailed feedback on code quality, security, performance, and best practices.

## Status

> 🚧 **WORK IN PROGRESS**: This repository is currently being converted from JavaScript to Python. Some features may not be fully functional during the transition process. The original JavaScript version is available at [ai-code-reviewer](https://github.com/PierrunoYT/ai-code-reviewer).

## Features

- 🤖 **Latest AI Models**: Uses GPT-4.1, Claude 4 Sonnet, Claude 3.7 Sonnet, and Gemini 2.5 Pro/Flash for intelligent code analysis
- 🔍 **Enhanced Analysis**: Reviews code quality, security, performance, accessibility, and dependency security
- 🌐 **Web Search Integration**: Real-time lookup of best practices and security vulnerabilities
- 🧠 **Extended Thinking**: Deep analysis with step-by-step reasoning (Anthropic)
- 📚 **Citations**: Source attribution for recommendations and best practices
- ⚡ **Batch Processing**: Efficient review of multiple commits simultaneously
- 🔄 **Retry Logic**: Robust error handling with exponential backoff
- 🪝 **Git Integration**: Automatic git hooks for pre-commit and pre-push reviews
- 📊 **Advanced Scoring**: Quality scores with confidence levels
- 🎯 **Highly Customizable**: Multiple provider configs and feature toggles
- 📄 **Markdown Reports**: Automatic saving of detailed review reports in markdown format
- 🚀 **Easy Setup**: Simple CLI installation and configuration

## Installation

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Set up your environment variables:**
   ```bash
   # Copy the example environment file
   cp .env.example .env

   # Edit .env and add your API keys
   # For Anthropic/Claude (recommended):
   export ANTHROPIC_API_KEY="your-anthropic-api-key"

   # For OpenAI:
   export OPENAI_API_KEY="your-openai-api-key"

   # For Google/Gemini:
   export GOOGLE_API_KEY="your-google-api-key"
   ```

3. **Install git hooks (optional but recommended):**
   ```bash
   npm run install-hook
   ```

## Usage

### Command Line Interface

**Review recent commits:**
```bash
# Review last commit
npm run review

# Review multiple commits
npm run review HEAD~3..HEAD

# Review specific commit range
npm run review abc1234..def5678
```

**Using the CLI directly:**
```bash
# Review with enhanced features
npx ai-reviewer review --provider anthropic --web-search --citations

# Review with batch processing
npx ai-reviewer review HEAD~5..HEAD --batch

# Review with extended thinking (Anthropic only)
npx ai-reviewer review --extended-thinking

# Save reviews to custom markdown directory
npx ai-reviewer review --markdown-dir ./my-reviews

# Disable markdown saving
npx ai-reviewer review --no-save-markdown

# Test the reviewer
npx ai-reviewer test

# Generate enhanced config file
npm run config

# Or use CLI directly for custom output
npx ai-reviewer config --enhanced -o .ai-reviewer-config.json

# Install git hooks
npm run install-hook

# Run demo to see new features
npm run demo
```

### Git Hooks

Once installed, the hooks will automatically:

- **Pre-commit**: Review staged changes before each commit
- **Pre-push**: Review all commits being pushed to remote

**Bypass hooks when needed:**
```bash
git commit --no-verify  # Skip pre-commit hook
git push --no-verify    # Skip pre-push hook
```

### Configuration

Create a `.ai-reviewer-config.json` file to customize settings:

> **Note**: Use `npm run config` to generate this file automatically.

```json
{
  "aiProvider": "anthropic",
  "model": "claude-sonnet-4-20250514",
  "maxTokens": 4000,
  "enableWebSearch": true,
  "enableExtendedThinking": true,
  "enableCitations": true,
  "enableBatchProcessing": true,
  "retryAttempts": 3,
  "batchSize": 5,
  "saveToMarkdown": true,
  "markdownOutputDir": "./code-reviews",
  "includeDiffInMarkdown": true,
  "reviewCriteria": [
    "code quality",
    "security vulnerabilities",
    "performance issues",
    "naming conventions",
    "code complexity",
    "test coverage",
    "documentation",
    "accessibility",
    "dependency security"
  ],
  "blockingIssues": ["critical", "high"],
  "minimumScore": 6,
  "alternativeConfigs": {
    "openai": {
      "aiProvider": "openai",
      "model": "gpt-4.1",
      "maxTokens": 4000,
      "enableWebSearch": true
    },
    "claude4opus": {
      "aiProvider": "anthropic",
      "model": "claude-opus-4-20250514",
      "maxTokens": 8000,
      "enableExtendedThinking": true,
      "enableCitations": true
    },
    "claude37sonnet": {
      "aiProvider": "anthropic",
      "model": "claude-3-7-sonnet-20250219",
      "maxTokens": 4000,
      "enableWebSearch": true,
      "enableCitations": true,
      "enableExtendedThinking": true
    },
    "gemini25pro": {
      "aiProvider": "google",
      "model": "gemini-2.5-pro-preview-05-06",
      "maxTokens": 4000,
      "enableWebSearch": true,
      "enableCitations": true,
      "enableExtendedThinking": true
    },
    "gemini25flash": {
      "aiProvider": "google",
      "model": "gemini-2.5-flash-preview-05-20",
      "maxTokens": 4000,
      "enableWebSearch": true,
      "enableCitations": true,
      "enableExtendedThinking": true
    }
  }
}
```

**Configuration Options:**
- `enableWebSearch`: Real-time web search for best practices
- `enableExtendedThinking`: Deep analysis with reasoning steps (Anthropic)
- `enableCitations`: Include source attribution in recommendations
- `enableBatchProcessing`: Process multiple commits efficiently
- `retryAttempts`: Number of retry attempts on API failures
- `batchSize`: Number of commits to process in each batch
- `saveToMarkdown`: Save detailed review reports in markdown format
- `markdownOutputDir`: Directory to save markdown review files
- `includeDiffInMarkdown`: Include code diffs in markdown reports

## Supported AI Providers

### Anthropic Claude (Recommended)
```bash
export ANTHROPIC_API_KEY="sk-ant-..."  # Your Anthropic API key
```

**Latest Models:**
- `claude-sonnet-4-20250514` - Latest Claude 4 Sonnet with enhanced capabilities (Default)
- `claude-opus-4-20250514` - Most powerful model with extended thinking
- `claude-3-7-sonnet-20250219` - Latest Claude 3.7 Sonnet with hybrid reasoning

**Exclusive Features:**
- Extended thinking for deeper analysis
- Citations with source attribution
- Computer use capabilities
- Batch processing API

### OpenAI
```bash
export OPENAI_API_KEY="sk-..."  # Your OpenAI API key
```

**Latest Models:**
- `gpt-4.1` - Latest GPT-4.1 with improved performance (Default)

**Features:**
- Web search integration
- Function calling
- Enhanced moderation

### Google AI (Gemini)
```bash
export GOOGLE_API_KEY="your-google-ai-api-key"  # Your Google AI API key
```

**Latest Models:**
- `gemini-2.5-pro-preview-05-06` - State-of-the-art thinking model with maximum accuracy
- `gemini-2.5-flash-preview-05-20` - Best price-performance with adaptive thinking

**Features:**
- Adaptive thinking with configurable budgets
- Multimodal understanding (text, images, video, audio)
- Long context windows (up to 1M tokens)
- Native tool use and function calling

## 📊 How Code Analysis Works

The AI reviewer performs comprehensive code analysis through a sophisticated multi-stage process:

### 1. **Git Data Extraction**
```javascript
// Extracts detailed commit information
- Commit hash, author, date, message, and body
- Full unified diff with 3 lines of context around changes
- Complete list of changed files
- File modification types (added, modified, deleted)
```

### 2. **Diff Analysis Structure**
The system uses `git show --unified=3` to capture:
- **Full diff content**: Including additions (+), deletions (-), and context lines
- **File paths**: What files were modified, added, or deleted
- **Line numbers**: Exact locations of changes
- **Change context**: Surrounding code for better understanding

### 3. **AI Prompt Construction**
Each commit receives a structured analysis prompt containing:

```
You are an expert code reviewer. Review this git commit:

Commit Message: [message]
Author: [author]  
Date: [date]

Code Changes:
```diff
[complete unified diff]
```

Analyze focusing on 8 key dimensions:
1. Code quality and maintainability
2. Security vulnerabilities (OWASP guidelines)
3. Performance implications  
4. Best practices adherence (current industry standards)
5. Testing considerations
6. Documentation needs
7. Accessibility considerations
8. Dependency security
```

### 4. **Enhanced Analysis Features**

**🌐 Web Search Integration** (optional):
- Real-time lookup of security vulnerabilities in dependencies
- Current best practices verification from authoritative sources
- Framework-specific recommendations and updates
- OWASP, NIST, and other security guideline references

**🧠 Extended Thinking** (Claude models):
- Step-by-step reasoning process visible to users
- Deeper analysis with logical thought progression
- Budget-controlled thinking tokens for thorough review

**📚 Citations & Sources**:
- Source attribution for all recommendations
- Links to security guidelines (OWASP, NIST, CWE)
- Best practice documentation references
- Framework and library documentation

### 5. **Multi-Dimensional Analysis Framework**

The AI analyzes **8 critical dimensions** simultaneously:

| Dimension | Analysis Focus | Examples |
|-----------|---------------|----------|
| **🔒 Security** | Vulnerabilities & threats | SQL injection, XSS, secrets in code, input validation |
| **⚡ Performance** | Efficiency & optimization | Inefficient algorithms, memory leaks, database queries |
| **🏗️ Quality** | Code structure & maintainability | Complexity, readability, design patterns, SOLID principles |
| **🎨 Style** | Conventions & consistency | Naming conventions, formatting, code organization |
| **🧪 Testing** | Test coverage & quality | Missing tests, test effectiveness, mocking strategies |
| **📚 Documentation** | Code clarity & docs | Comments, README updates, API documentation |
| **♿ Accessibility** | Inclusive design | ARIA labels, keyboard navigation, screen reader support |
| **📦 Dependencies** | Package security & updates | Vulnerable packages, outdated versions, license issues |

### 6. **Context-Aware Intelligence**

The AI understands and adapts to:

**Language-Specific Patterns:**
- JavaScript/TypeScript: Async/await, promises, ES6+ features
- Python: Pythonic idioms, PEP standards, virtual environments
- Java: Spring patterns, Maven/Gradle, enterprise patterns
- And 50+ other programming languages

**Framework Recognition:**
- **Web**: React, Vue, Angular, Express, Django, Flask
- **Mobile**: React Native, Flutter, Swift, Kotlin
- **Cloud**: AWS, Azure, GCP services and patterns
- **Databases**: SQL patterns, NoSQL usage, ORM practices

**Security Context Analysis:**
- Web application security (OWASP Top 10)
- API security best practices
- Database security patterns
- Authentication and authorization flows

### 7. **Structured Analysis Output**

Returns comprehensive JSON structure:
```json
{
  "score": 7,                    // 1-10 quality rating
  "confidence": 9,               // AI confidence level
  "summary": "Added authentication with security concerns",
  "issues": [
    {
      "severity": "critical",    // critical|high|medium|low
      "description": "SQL injection vulnerability",
      "suggestion": "Use parameterized queries",
      "category": "security",    // security|performance|quality|style|testing|documentation
      "citation": "OWASP SQL Injection Prevention",
      "autoFixable": true
    }
  ],
  "suggestions": ["Add input validation", "Implement rate limiting"],
  "security": ["Use HTTPS", "Hash passwords with bcrypt"],
  "performance": ["Add database indexing", "Implement caching"],
  "dependencies": ["Update vulnerable packages"],
  "accessibility": ["Add ARIA labels", "Improve keyboard navigation"],
  "sources": ["OWASP Top 10", "Node.js Security Checklist"]
}
```

### 8. **Real-World Analysis Examples**

**Example 1: Authentication Code**
```javascript
// Input: User login function with SQL concatenation
function login(username, password) {
  const query = "SELECT * FROM users WHERE username = '" + username + "'";
  return database.query(query);
}

// AI Analysis Output:
// 🚨 CRITICAL: SQL injection vulnerability
// 💡 Suggestion: Use parameterized queries
// 📚 Source: OWASP SQL Injection Prevention Guide
// 🔧 Auto-fixable: Yes
```

**Example 2: React Component**
```jsx
// Input: Component without accessibility
<button onClick={handleClick}>Submit</button>

// AI Analysis Output:
// ⚠️ MEDIUM: Missing accessibility attributes
// 💡 Suggestion: Add aria-label and keyboard support
// 📚 Source: WAI-ARIA Authoring Practices
// ♿ Accessibility: Consider screen reader users
```

### 9. **Intelligent Scoring System**

**Quality Score (1-10):**
- **8-10**: Excellent code with minor suggestions
- **6-7**: Good code with some improvements needed
- **4-5**: Acceptable but requires attention
- **1-3**: Significant issues requiring immediate fixes

**Confidence Level (1-10):**
- **8-10**: High confidence in analysis accuracy
- **6-7**: Good confidence with some uncertainty
- **4-5**: Moderate confidence, manual review suggested
- **1-3**: Low confidence, human expert review required

The analysis is **comprehensive, context-aware, and actionable** - providing expert-level code review insights with the latest security knowledge and best practices, far beyond simple syntax checking.

## Enhanced Review Output

The AI reviewer provides comprehensive analysis:

- **Quality Score**: 1-10 rating of code quality
- **Confidence Level**: AI's confidence in the review (1-10)
- **Summary**: Brief overview of the changes
- **Categorized Issues**: Problems with severity, category, and auto-fix indicators
- **Suggestions**: Improvement recommendations
- **Security Notes**: Security-related observations
- **Performance Notes**: Performance implications
- **Dependency Notes**: Package and library security
- **Accessibility Notes**: Accessibility considerations
- **Citations**: Source attribution for recommendations

## 📄 Markdown Review Reports

All reviews are automatically saved as detailed markdown files in the `./code-reviews` directory (configurable). Each report includes:

- **Complete review details** with all scores, issues, and suggestions
- **Formatted markdown** with proper headings, emojis, and structure
- **Code diffs** (optional, enabled by default)
- **Timestamped filenames** for easy organization
- **Provider and model information** in footer

**Example filename format:**
```
2025-05-30T14-30-15-abc12345-fix-authentication-bug.md
```

**Report structure:**
- 📊 Review Scores (Quality & Confidence)
- 📋 Summary
- ⚠️ Issues Found (categorized by severity)
- 💡 General Suggestions
- 🔒 Security Notes
- ⚡ Performance Notes
- 📦 Dependency Notes
- ♿ Accessibility Notes
- 📚 Sources Consulted
- 📝 Code Changes (diff)

Example enhanced output:
```
📊 Code Quality Score: 7/10
🎯 Confidence Level: 9/10

📋 Summary: Added user authentication endpoint with password validation

⚠️  Issues Found:
  1. 🚨 CRITICAL: SQL injection vulnerability in getUserData function
     💡 Suggestion: Use parameterized queries instead of string concatenation
     🏷️  Category: security
     📚 Source: OWASP SQL Injection Prevention Cheat Sheet
     🔧 Auto-fixable: Yes

  2. ⚠️ HIGH: Hardcoded JWT secret key
     💡 Suggestion: Use environment variables for secrets
     🏷️  Category: security
     📚 Source: NIST Cybersecurity Framework

💡 Suggestions:
  1. Add input validation for user parameters
  2. Implement rate limiting for authentication attempts
  3. Add comprehensive unit tests

🔒 Security Notes:
  1. Missing authentication middleware on sensitive endpoints
  2. Password complexity requirements not enforced

⚡ Performance Notes:
  1. Consider implementing connection pooling for database queries

📦 Dependency Notes:
  1. bcrypt version should be updated to latest for security patches

♿ Accessibility Notes:
  1. Authentication forms should include proper ARIA labels

📚 Sources Consulted:
  1. OWASP Authentication Cheat Sheet
  2. Node.js Security Best Practices
  3. JWT Security Best Practices
```

## Development

**Project Structure:**
```
src/
├── index.js              # Main application entry point
├── ai-reviewer.js        # AI integration and API calls
├── git-analyzer.js       # Git operations and diff analysis
├── cli.js               # Command line interface
├── config-loader.js      # Configuration management
├── demo.js              # Demo script showcasing features
└── git-hook-installer.js # Git hooks management

Configuration Files:
├── .ai-reviewer-config.json  # Main configuration file
├── .env.example             # Environment variables template
├── package.json             # Node.js dependencies and scripts
└── .gitignore              # Git ignore patterns
```

**Scripts:**
```bash
npm start          # Run the reviewer
npm run review     # Review commits
npm run install-hook # Install git hooks
npm test          # Run tests with sample code
npm run demo      # Run demo showcasing enhanced features
npm run config    # Generate enhanced configuration file (outputs to .ai-reviewer-config.json)
```

## Environment Variables

### Required API Keys (choose one or more providers)
- `ANTHROPIC_API_KEY` - Your Anthropic/Claude API key
- `OPENAI_API_KEY` - Your OpenAI API key
- `GOOGLE_API_KEY` - Your Google/Gemini API key
- `AI_API_KEY` - Legacy fallback API key (for backward compatibility)

### Optional Configuration
- `AI_PROVIDER` - AI provider ('anthropic', 'openai', or 'google') - defaults to 'anthropic'
- `AI_MODEL` - AI model to use - defaults to provider-specific latest model
- `DEBUG` - Enable debug logging (true/false) - defaults to false
- `AI_REVIEWER_CONFIG_PATH` - Custom config file path - defaults to '.ai-reviewer-config.json'
- `JWT_SECRET` - JWT secret for demo authentication scenarios

## Troubleshooting

**Common Issues:**

1. **"AI API key not found"**
   - Set the appropriate API key environment variable:
     - `ANTHROPIC_API_KEY` for Claude models
     - `OPENAI_API_KEY` for GPT models
     - `GOOGLE_API_KEY` for Gemini models
   - Or specify `--api-key` in CLI command
   - Or use the CLI `--api-key` parameter

2. **Git hooks not working**
   - Ensure you're in a git repository
   - Run `npm run install-hook` to reinstall hooks
   - Check hook permissions on Unix systems

3. **Reviews taking too long**
   - Reduce `maxTokens` in configuration
   - Use a faster AI model
   - Review smaller commit ranges

4. **False positives in reviews**
   - Customize `reviewCriteria` in configuration
   - Adjust `minimumScore` threshold
   - Use `--no-verify` to bypass when needed

## Security Considerations

- **API Keys**: Never commit your `.env` file or expose API keys in code
- **Environment Variables**: Use `.env.example` as a template and create your own `.env` file
- **Git Hooks**: The pre-commit and pre-push hooks help catch security issues before they're committed
- **Configuration**: Review the `.ai-reviewer-config.json` file to ensure it meets your security requirements
- **Backup**: Git hooks create backup files (`.backup` extension) when installing over existing hooks

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

The AI reviewer will automatically review your PR! 🎉
