# Setting Up Python 3.10.7

Your system currently has Python 3.13.7, but the project requires Python 3.10.7 for compatibility with dependencies (especially scikit-learn).

## Option 1: Using pyenv (Recommended)

### Step 1: Install pyenv (if not installed)

```bash
# Install pyenv using Homebrew
brew install pyenv

# Add to your shell profile (~/.zshrc or ~/.bash_profile)
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc

# Reload shell
source ~/.zshrc
```

### Step 2: Install Python 3.10.7

```bash
# Install Python 3.10.7
pyenv install 3.10.7

# Set it as local version for this project
cd /Users/vineet/Documents/CMPE272/Project/Synergy_CMPE272
pyenv local 3.10.7

# Verify
python --version  # Should show Python 3.10.7
```

### Step 3: Recreate Virtual Environment

```bash
# Remove old venv
cd backend
rm -rf venv

# Create new venv with Python 3.10.7
python3.10 -m venv venv

# Activate
source venv/bin/activate

# Verify Python version
python --version  # Should show Python 3.10.7

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Option 2: Using Homebrew (Alternative)

### Step 1: Install Python 3.10

```bash
# Install Python 3.10
brew install python@3.10

# Verify installation
python3.10 --version
```

### Step 2: Create Virtual Environment

```bash
cd backend
rm -rf venv

# Create venv with Python 3.10
python3.10 -m venv venv

# Activate
source venv/bin/activate

# Verify
python --version  # Should show Python 3.10.x

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Option 3: Using Docker (No Local Python Needed)

If you prefer not to install Python 3.10.7 locally, you can use Docker which already has Python 3.11 configured:

```bash
# Just use Docker Compose - it handles Python version
cd infrastructure/docker
docker-compose -f docker-compose.microservices.yml up -d
```

---

## Quick Fix Script

I'll create a script to automate this. Run:

```bash
./scripts/setup_python_3.10.sh
```

---

## Verify Setup

After setup, verify:

```bash
cd backend
source venv/bin/activate
python --version  # Should show Python 3.10.7
python -c "import sklearn; print(sklearn.__version__)"  # Should work
```

---

## Troubleshooting

### Issue: "pyenv: command not found"
- Make sure pyenv is installed and in your PATH
- Restart your terminal
- Run: `eval "$(pyenv init -)"`

### Issue: "Python 3.10.7 build failed"
- Install build dependencies: `brew install openssl readline sqlite3 xz zlib`
- Try: `pyenv install 3.10.7 --verbose`

### Issue: "pip install fails"
- Upgrade pip: `python -m pip install --upgrade pip`
- Try installing numpy first: `pip install numpy==1.26.4`
- Then install requirements: `pip install -r requirements.txt`

