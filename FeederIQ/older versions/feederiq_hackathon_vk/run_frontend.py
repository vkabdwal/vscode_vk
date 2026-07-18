"""Launch the FeederIQ Streamlit frontend."""
import subprocess
import sys

if __name__ == "__main__":
    subprocess.run([sys.executable, "-m", "streamlit", "run", "feederiq/frontend/app.py", "--server.port", "8501"])
