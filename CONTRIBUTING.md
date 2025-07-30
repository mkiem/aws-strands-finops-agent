# Contributing to FinOps Agent

Thank you for your interest in contributing to FinOps Agent! We welcome contributions from the community and are grateful for your support.

## 🤝 **How to Contribute**

### Reporting Issues

Before creating an issue, please:

1. **Search existing issues** to avoid duplicates
2. **Use the issue templates** when available
3. **Provide detailed information** including:
   - Steps to reproduce the issue
   - Expected vs actual behavior
   - Environment details (OS, Python version, AWS region)
   - Relevant logs or error messages

### Suggesting Features

We love feature suggestions! Please:

1. **Check existing feature requests** first
2. **Use the feature request template**
3. **Explain the use case** and why it would be valuable
4. **Consider the scope** - smaller, focused features are easier to implement

### Contributing Code

1. **Fork the repository**
2. **Create a feature branch** from `main`
3. **Make your changes**
4. **Test your changes** thoroughly
5. **Submit a pull request**

## 🛠️ **Development Setup**

### Prerequisites

- Python 3.11+
- Node.js 18+
- AWS CLI configured
- Git

### Local Development

1. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/finopsagent.git
   cd finopsagent
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.template .env
   # Edit .env with your configuration
   ```

4. **Install frontend dependencies**
   ```bash
   cd finops-ui
   npm install
   cd ..
   ```

5. **Run tests**
   ```bash
   # Python tests
   python -m pytest
   
   # Frontend tests
   cd finops-ui
   npm test
   ```

### Project Structure

```
finopsAgent/
├── docs/                           # Documentation
├── examples/                       # Usage examples
├── finops-ui/                      # React frontend
├── supervisor_agent/               # Main orchestration agent
├── aws-cost-forecast-agent/        # Cost forecasting
├── trusted_advisor_agent/          # AWS optimization recommendations
├── budget_management_agent/        # Budget analysis
├── websocket_api/                  # Real-time API
├── requirements.txt                # Python dependencies
└── .env.template                   # Environment template
```

## 📝 **Coding Standards**

### Python Code

- **Follow PEP 8** style guidelines
- **Use type hints** where appropriate
- **Write docstrings** for functions and classes
- **Keep functions focused** and single-purpose
- **Use meaningful variable names**

Example:
```python
def calculate_cost_forecast(
    historical_data: List[CostData], 
    months: int = 12
) -> ForecastResult:
    """
    Calculate cost forecast based on historical data.
    
    Args:
        historical_data: List of historical cost data points
        months: Number of months to forecast (default: 12)
        
    Returns:
        ForecastResult containing predicted costs and confidence intervals
    """
    # Implementation here
    pass
```

### JavaScript/React Code

- **Use ES6+ features**
- **Follow React best practices**
- **Use functional components** with hooks
- **Write meaningful component names**
- **Add PropTypes** or TypeScript types

Example:
```javascript
const CostChart = ({ data, timeRange }) => {
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    // Effect logic here
  }, [data, timeRange]);
  
  return (
    <div className="cost-chart">
      {/* Component JSX */}
    </div>
  );
};
```

### Documentation

- **Use clear, concise language**
- **Include code examples**
- **Update relevant documentation** when making changes
- **Use proper markdown formatting**

## 🧪 **Testing**

### Running Tests

```bash
# Run all Python tests
python -m pytest

# Run specific test file
python -m pytest tests/test_supervisor_agent.py

# Run with coverage
python -m pytest --cov=.

# Run frontend tests
cd finops-ui
npm test
```

### Writing Tests

- **Write tests for new features**
- **Update tests when modifying existing code**
- **Use descriptive test names**
- **Mock external dependencies** (AWS APIs, etc.)

Example:
```python
def test_cost_forecast_calculation():
    """Test that cost forecast calculates correctly with valid data."""
    # Arrange
    historical_data = [
        CostData(date="2024-01-01", amount=100.0),
        CostData(date="2024-02-01", amount=110.0),
    ]
    
    # Act
    result = calculate_cost_forecast(historical_data, months=6)
    
    # Assert
    assert result.forecast_months == 6
    assert len(result.predictions) == 6
    assert all(p.amount > 0 for p in result.predictions)
```

## 📋 **Pull Request Process**

### Before Submitting

1. **Ensure tests pass** locally
2. **Update documentation** if needed
3. **Add/update tests** for your changes
4. **Follow the coding standards**
5. **Rebase your branch** on the latest main

### Pull Request Template

When submitting a PR, please include:

- **Clear description** of what the PR does
- **Link to related issues** (if applicable)
- **Screenshots** for UI changes
- **Testing notes** - how you tested the changes
- **Breaking changes** - if any

### Review Process

1. **Automated checks** must pass (tests, linting)
2. **Code review** by maintainers
3. **Address feedback** promptly
4. **Squash commits** if requested
5. **Merge** once approved

## 🏷️ **Commit Messages**

Use clear, descriptive commit messages:

```
feat: add cost forecasting for EC2 instances

- Implement 12-month cost prediction algorithm
- Add support for multiple instance types
- Include confidence intervals in results

Fixes #123
```

### Commit Types

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

## 🌟 **Recognition**

Contributors are recognized in:

- **README.md** acknowledgments
- **Release notes** for significant contributions
- **GitHub contributors** page

## 📞 **Getting Help**

If you need help:

1. **Check the documentation** in the `docs/` folder
2. **Search existing issues** and discussions
3. **Ask in GitHub Discussions**
4. **Join our community** (links in README)

## 📜 **Code of Conduct**

Please note that this project is released with a [Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project, you agree to abide by its terms.

## 🎯 **Good First Issues**

Look for issues labeled `good first issue` - these are perfect for new contributors!

## 📈 **Development Roadmap**

Check our [project roadmap](https://github.com/finopsagent/finopsagent/projects) to see what we're working on and where you can help.

---

Thank you for contributing to FinOps Agent! 🚀
