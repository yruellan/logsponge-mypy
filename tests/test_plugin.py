import subprocess
import os
import pytest

# Define paths relative to the test file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TYPED_DATA_DIR = os.path.join(BASE_DIR, "tests")

def run_mypy(file_name):
    """Runs mypy on a specific file and returns (exit_code, stdout, stderr)."""
    file_path = os.path.join(TYPED_DATA_DIR, file_name)
    config_path = os.path.join(BASE_DIR, "mypy.ini")
    
    result = subprocess.run(
        ["mypy", file_path, "--config-file", config_path, "--no-incremental"],
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr

@pytest.mark.parametrize("filename", ["hw1.py", "hw2.py"])
def test_valid_streams_pass(filename):
    """
    These files contain valid streams and should pass Mypy check with code 0.
    """
    exit_code, stdout, stderr = run_mypy(filename)
    
    if exit_code != 0:
        pytest.fail(f"Mypy failed on valid file {filename}:\n{stdout}\n{stderr}")

def test_generics_mismatch_fails():
    """
    hw4.py contains invalid compositions. Mypy SHOULD fail here.
    We also check that it fails with YOUR specific plugin error.
    """
    exit_code, stdout, stderr = run_mypy("hw4.py")
    
    # 1. Assert failure (Exit code should be 1 because of type errors)
    assert exit_code != 0, f"Mypy should have failed on hw4.py but passed.\n{stdout}"
    
    # 2. Assert your plugin is triggering (check for your specific error message)
    # Based on your plugin.py logic, the error starts with "Stream mismatch"
    assert "Stream mismatch" in stdout, "Did not find expected plugin error message 'Stream mismatch'"
    
    # Optional: Be more specific about the error
    # assert "expected key 'y'" in stdout

def test_1():
    """
    A simple test to ensure that the test setup is working correctly.
    """
    assert 1 + 1 == 2, "Basic arithmetic failed, something is wrong with the test setup."