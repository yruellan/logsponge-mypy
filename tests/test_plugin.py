import subprocess
import os
import re
import pytest
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS_DIR = os.path.join(BASE_DIR, "tests")

def parse_expected_errors(file_path):
    """
    Reads the file and looks for comments like '# E: <message>'.
    Returns a dict: { line_number: "expected message substring" }
    """
    expected = {}
    with open(file_path, "r") as f:
        for i, line in enumerate(f, start=1):
            if "# E:" in line:
                # Extract the message after # E:
                parts = line.split("# E:", 1)
                msg = parts[1].strip()
                expected[i] = msg
    return expected

def parse_actual_errors(stdout):
    """
    Parses Mypy output.
    Returns a dict: { line_number: ["error message 1", "error message 2"] }
    """
    # Regex to capture: filename:line: error: message
    # We only care about errors (not notes)
    regex = re.compile(r"^.*:(\d+):\s+error:\s+(.*)$")
    actual = defaultdict(list)
    
    for line in stdout.splitlines():
        match = regex.match(line)
        if match:
            line_num = int(match.group(1))
            message = match.group(2)
            actual[line_num].append(message)
    return actual

def run_mypy_and_compare(filename):
    file_path = os.path.join(TESTS_DIR, filename)
    config_path = os.path.join(BASE_DIR, "mypy.ini")
    
    # 1. Parse expectations from source code
    expected_errors = parse_expected_errors(file_path)
    
    # 2. Run Mypy
    result = subprocess.run(
        ["mypy", file_path, "--config-file", config_path, "--no-incremental", "--hide-error-codes"],
        capture_output=True,
        text=True
    )
    
    # 3. Parse actual errors from Mypy output
    actual_errors = parse_actual_errors(result.stdout)
    
    # 4. Compare
    errors = []
    
    # Check if expected errors occurred
    for line_num, expected_msg in expected_errors.items():
        if line_num not in actual_errors:
            errors.append(f"Line {line_num}: Expected error '{expected_msg}' but got PASSED.")
        else:
            # Check if the message matches
            found = False
            for actual_msg in actual_errors[line_num]:
                if expected_msg in actual_msg:
                    found = True
                    break
            if not found:
                errors.append(f"Line {line_num}: Expected '{expected_msg}' but got '{actual_errors[line_num]}'")

    # Check for unexpected errors (false positives)
    for line_num, msgs in actual_errors.items():
        if line_num not in expected_errors:
            errors.append(f"Line {line_num}: Unexpected error reported: {msgs}")

    if errors:
        pytest.fail(f"Test failed for {filename}:\n" + "\n".join(errors))

# --- Tests ---

@pytest.mark.parametrize("filename", ["hw1.py", "hw2.py"])
def test_valid_files(filename):
    """Ensure these files have ZERO errors."""
    run_mypy_and_compare(filename)

def test_generics_failures():
    """Ensure hw4.py has exactly the errors marked with '# E:'."""
    run_mypy_and_compare("hw4.py")