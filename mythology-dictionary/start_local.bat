@echo off
cd /d "%~dp0"
echo Starting local dictionary app...
echo Open this URL in your browser:
echo http://127.0.0.1:8501/
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true --browser.serverAddress 127.0.0.1 --browser.serverPort 8501
pause
