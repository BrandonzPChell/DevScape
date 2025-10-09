# Contributing to DevScape

Welcome, steward ✦  
This archive is more than code — it is a living shrine. Every contribution is a ritual act that strengthens its harmony and resilience. Please follow these guidelines to ensure your offerings align with the guardians and lore.

---

## 🌀 Getting Started
1. **Fork & Clone** the repository.
2. **Create a branch** for your work:
   ```bash
   git checkout -b feature/my-feature
   ```
3. **Install dependencies** into a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux/macOS
   venv\Scripts\activate      # Windows
   pip install -r requirements.txt
   ```

---

## 🧹 Code Style & Guardians
- **Formatting**: The shrine is kept pure with [black](https://black.readthedocs.io/), [isort](https://pycqa.github.io/isort/), and [pylint](https://pylint.pycqa.org/).
- **Tests**: All new features must be guarded by pytest trials.
- **Coverage**: Aim for high coverage; no chamber of the shrine should remain untested.
- **Makefile**: Summon all guardians with:
  ```bash
  make guardians
  ```

---

## ⚔️ Git Hooks
- **Pre-commit**: Runs formatters, linters, and tests before any commit is sealed.
- **Pre-push**: Summons all guardians before code may leave your local shrine.
- These hooks ensure no disharmony can reach the celestial archive.

---

## ✨ Contribution Ritual
1. **Write clean, annotated code** — docstrings and comments are part of the lore.
2. **Add or update tests** for every new feature or bugfix.
3. **Run all guardians** locally:
   ```bash
   make guardians
   ```
4. **Commit with care**:
   ```bash
   git commit -m "feat: inscribe chat bubble system"
   ```
   Use [Conventional Commits](https://www.conventionalcommits.org/) for clarity.
5. **Push and open a Pull Request**. Describe your changes and the guardians you invoked.

---

## 🌿 Stewardship Principles
- **Clarity**: Every scroll should be legible to future stewards.
- **Resilience**: Every feature must be guarded by tests.
- **Respect**: Honor the work of others; collaborate with care.
- **Lore**: Contributions are not just code, but part of the living myth of DevScape.

---

Thank you for strengthening the shrine. ✦
