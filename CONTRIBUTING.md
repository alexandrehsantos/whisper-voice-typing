# Contributing to Whisper Voice Typing

Thank you for your interest in contributing! This project welcomes contributions from everyone.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/alexandrehsantos/whisper-voice-typing/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - System information (OS, Python version, etc.)
   - Relevant logs

### Suggesting Features

1. Check existing [Issues](https://github.com/alexandrehsantos/whisper-voice-typing/issues) and [Pull Requests](https://github.com/alexandrehsantos/whisper-voice-typing/pulls)
2. Create a new issue describing:
   - The feature and its benefits
   - Use cases
   - Possible implementation approach

### Code Contributions

1. **Fork the repository**
   ```bash
   gh repo fork alexandrehsantos/whisper-voice-typing --clone
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow existing code style
   - Add comments for complex logic
   - Update documentation if needed

4. **Test your changes**
   ```bash
   # Run the daemon in foreground
   python3 voice-daemon.py

   # Test basic functionality
   # - Trigger hotkey
   # - Speak test phrase
   # - Verify transcription
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add feature: brief description"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**
   - Go to your fork on GitHub
   - Click "New Pull Request"
   - Describe your changes clearly
   - Reference related issues

## Code Style

- Follow PEP 8 for Python code
- Use meaningful variable names
- Keep functions focused and small
- Add docstrings to functions and classes
- Use type hints where appropriate

## Commit Message Guidelines

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- First line should be concise (50 chars or less)
- Add detailed description if needed

Examples:
```
Add support for custom vocabulary

Fix memory leak in audio recording
- Use NamedTemporaryFile instead of mktemp
- Properly close PyAudio streams

Update README with installation instructions
```

## Pull Request Process

1. Ensure your PR addresses a single concern
2. Update README.md if you change functionality
3. The PR will be reviewed by maintainers
4. Address any feedback
5. Once approved, it will be merged

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/whisper-voice-typing.git
cd whisper-voice-typing

# Install dependencies
pip install -r requirements.txt

# Run in development mode
python3 voice-daemon.py
```

## Areas Needing Help

- Multi-language support
- Windows/macOS compatibility
- GUI configuration tool
- Performance optimizations
- Documentation improvements
- Test coverage

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Assume good intentions

## Questions?

Feel free to:
- Open an issue for questions
- Start a discussion in GitHub Discussions
- Comment on relevant issues/PRs

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
