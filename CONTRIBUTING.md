# Contributing to Watch Media Server

Thank you for your interest in contributing to Watch Media Server! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Docker (for testing)
- Git
- Basic knowledge of Flask, HTML/CSS/JavaScript

### Development Setup

1. **Fork and Clone**:
   ```bash
   git clone https://github.com/your-username/watch-media-server.git
   cd watch-media-server
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Development Server**:
   ```bash
   python app.py --debug
   ```

## 📝 How to Contribute

### Types of Contributions

1. **Bug Reports**: Report issues you encounter
2. **Feature Requests**: Suggest new features
3. **Code Contributions**: Submit pull requests
4. **Documentation**: Improve documentation
5. **Testing**: Help test new features

### Reporting Issues

When reporting bugs, please include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- System information (OS, Python version, etc.)
- Relevant logs or error messages

### Feature Requests

For feature requests, please:
- Describe the feature clearly
- Explain why it would be useful
- Consider implementation complexity
- Check if similar features exist

## 🔧 Development Guidelines

### Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add comments for complex logic
- Keep functions small and focused

### Git Workflow

1. **Create Feature Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**:
   - Write clean, tested code
   - Update documentation if needed
   - Add tests for new features

3. **Commit Changes**:
   ```bash
   git add .
   git commit -m "Add: brief description of changes"
   ```

4. **Push and Create PR**:
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Format

Use clear, descriptive commit messages:
- `Add: new feature description`
- `Fix: bug description`
- `Update: what was updated`
- `Remove: what was removed`
- `Docs: documentation changes`

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_app.py

# Run with coverage
python -m pytest --cov=app
```

### Test Structure

```
tests/
├── test_app.py          # Main application tests
├── test_media_manager.py # Media manager tests
├── test_formatter.py    # Media formatter tests
└── fixtures/            # Test data
```

## 📚 Documentation

### Documentation Standards

- Use clear, concise language
- Include code examples
- Update README.md for major changes
- Add docstrings to new functions
- Update installation guides for new requirements

### Documentation Files

- `README.md` - Main project documentation
- `UNRAID_INSTALLATION.md` - Unraid setup guide
- `PROJECT_OVERVIEW.md` - Feature overview
- `CONTRIBUTING.md` - This file
- Inline code comments and docstrings

## 🐳 Docker Development

### Building Docker Image

```bash
docker build -t watch-media-server:dev .
```

### Testing with Docker

```bash
# Run with Docker Compose
docker-compose up -d

# Run tests in container
docker run --rm watch-media-server:dev python -m pytest
```

## 🔍 Code Review Process

### Pull Request Guidelines

1. **Description**: Clear description of changes
2. **Testing**: Include test results
3. **Documentation**: Update relevant docs
4. **Breaking Changes**: Clearly mark any breaking changes
5. **Screenshots**: For UI changes

### Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No breaking changes (or clearly marked)
- [ ] Security considerations addressed

## 🚨 Security

### Security Guidelines

- Never commit sensitive information (API keys, passwords)
- Validate all user inputs
- Use parameterized queries for database operations
- Follow security best practices for web applications

### Reporting Security Issues

For security vulnerabilities, please:
- Email security issues privately
- Do not create public issues for security problems
- Include detailed reproduction steps
- Allow time for fixes before public disclosure

## 📋 Project Structure

```
watch-media-server/
├── app.py                 # Main Flask application
├── console.py             # CLI interface
├── media_formatter.py     # File organization
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose setup
├── watch-template.xml    # Unraid template
├── templates/            # HTML templates
├── static/               # CSS, JS, images
├── tests/                # Test files
├── docs/                 # Documentation
└── scripts/              # Utility scripts
```

## 🎯 Areas for Contribution

### High Priority
- User authentication and authorization
- Advanced transcoding features
- Mobile-responsive improvements
- Performance optimizations
- Additional metadata sources

### Medium Priority
- Plugin system
- API improvements
- Additional file format support
- Enhanced search functionality
- Backup and restore features

### Low Priority
- Theme customization
- Advanced playlist features
- Integration with external services
- Advanced analytics
- Multi-language support

## 💬 Communication

### Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Pull Requests**: For code contributions

### Community Guidelines

- Be respectful and inclusive
- Help others when possible
- Follow the code of conduct
- Provide constructive feedback

## 📄 License

By contributing to Watch Media Server, you agree that your contributions will be licensed under the MIT License.

## 🙏 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Project documentation

Thank you for contributing to Watch Media Server! 🎬
