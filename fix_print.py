import re
from pathlib import Path

def add_flush_to_prints(file_path):
    """Add flush=True to all print() calls in a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace print(...) with print(..., flush=True)
    # But avoid replacing if flush=True already exists
    def replace_print(match):
        full_match = match.group(0)
        if 'flush=' in full_match:
            return full_match  # Already has flush parameter
        # Insert flush=True before the closing parenthesis
        return full_match[:-1] + ', flush=True)'

    # Match print(...) calls, handling nested parentheses
    pattern = r'print\([^)]*\)'
    new_content = re.sub(pattern, replace_print, content)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"Updated {file_path}")

# Files to update
files = [
    'research_agent/skills/diagram_generator.py',
    'run_web.py'
]

for file in files:
    file_path = Path(file)
    if file_path.exists():
        add_flush_to_prints(file_path)
    else:
        print(f"File not found: {file}")
