# Contributing to BAGO Framework

Thank you for your interest in contributing to BAGO Framework! This guide covers the basics. For the full extended guide, see [`.bago/docs/CONTRIBUTING.md`](.bago/docs/CONTRIBUTING.md).

---

## 🐛 Opening Issues

- Use the GitHub issue tracker: [MarcValls/bago-framework/issues](https://github.com/MarcValls/bago-framework/issues)
- Search for existing issues before opening a new one.
- Use the issue templates when available (bug report, feature request).
- Include BAGO version (`./bago health` output), OS, and Python version.

---

## 🔀 Proposing Changes

1. **Fork** the repository and create a branch from `master`.
2. Make your changes following the existing code style.
3. Run `./bago pre-push` and ensure it exits green before opening a PR.
4. Open a Pull Request against `master` with a clear description of what changed and why.
5. Link any related issues in the PR description.

### Pre-push checklist

```bash
./bago validate   # Validates pack integrity
./bago health     # Must score ≥ 90/100
./bago pre-push   # Full pre-push guard — must pass
```

---

## 🤖 For AI Agents

If you are a GitHub Copilot agent or similar AI assistant working in this repo, read [`.bago/AGENT_START.md`](.bago/AGENT_START.md) first. It contains the mandatory session bootstrap protocol.

---

## 📄 License

By contributing you agree that your contributions will be licensed under the [MIT License](LICENSE).
