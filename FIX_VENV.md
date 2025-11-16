# Fix: Using Correct Python 3.10 Virtual Environment

You have two virtual environments:
- `.venv` in root (Python 3.13) ❌
- `backend/venv` (Python 3.10.19) ✅

## Solution: Use the Backend Virtual Environment

### Option 1: Deactivate and Use Backend Venv (Recommended)

```bash
# Deactivate current venv
deactivate

# Navigate to backend
cd backend

# Activate the correct venv
source venv/bin/activate

# Verify
python --version  # Should show: Python 3.10.19
```

### Option 2: Update Root .venv to Python 3.10

If you prefer to use `.venv` in the root:

```bash
# Deactivate current
deactivate

# Remove old .venv
rm -rf .venv

# Create new .venv with Python 3.10
python3.10 -m venv .venv

# Activate
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt

# Verify
python --version  # Should show: Python 3.10.19
```

## Quick Fix Command

```bash
deactivate && cd backend && source venv/bin/activate && python --version
```

