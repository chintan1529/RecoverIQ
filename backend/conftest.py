import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Configure test environment variables for automated pytest suites
os.environ["RECOVERIQ_OPERATOR_KEYS"] = "test_operator_key,test_rzp_operator_key"
os.environ["RECOVERIQ_ADMIN_KEYS"] = "test_admin_key,test_rzp_admin_key"
