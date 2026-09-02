@echo off
REM install.bat — Content Strategist Agent Installer (Windows)
REM Run: install.bat

echo 📦 Content Strategist Agent — Installer
echo =======================================
echo.

REM Check Python version
python --version 2>nul
if errorlevel 1 (
    echo ❌ Python not found. Install from python.org
    exit /b 1
)

for /f "tokens=2 delims= " %%a in ('python --version') do set PYTHON_VERSION=%%a
echo 🐍 Python version: %PYTHON_VERSION%

REM Check version >= 3.10
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
)
if %MAJOR% LSS 3 (
    echo ❌ Python 3.10+ required. Found %PYTHON_VERSION%
    exit /b 1
)
if %MAJOR% EQU 3 if %MINOR% LSS 10 (
    echo ❌ Python 3.10+ required. Found %PYTHON_VERSION%
    exit /b 1
)

REM Create virtual environment
set VENV_DIR=.venv
if not exist "%VENV_DIR%" (
    echo 🔧 Creating virtual environment...
    python -m venv %VENV_DIR%
) else (
    echo ✅ Virtual environment exists
)

REM Activate
call %VENV_DIR%\Scripts\activate.bat

REM Upgrade pip
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1

REM Install dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt

REM Create directories
if not exist config mkdir config
if not exist state mkdir state
if not exist output mkdir output
if not exist transcripts mkdir transcripts

REM Copy templates to config
if not exist config\tone_of_voice.yaml (
    echo 📝 Creating config from templates...
    copy templates\tone_of_voice.yaml config\tone_of_voice.yaml
    copy templates\feeds.yaml config\feeds.yaml
)

REM Create .env template
if not exist .env (
    echo 📝 Creating .env template...
    echo # Content Strategist Agent — Environment Variables> .env
    echo # Copy this file to .env and fill in your values>> .env
    echo.>> .env
    echo # Required for Module 2 (Radar)>> .env
    echo YOUTUBE_API_KEY=your_youtube_data_api_v3_key_here>> .env
    echo TWITTER_BEARER_TOKEN=your_twitter_api_v2_bearer_token_here>> .env
    echo.>> .env
    echo # Webhooks (choose one)>> .env
    echo SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/XXX/XXX>> .env
    echo REM TELEGRAM_BOT_TOKEN=123456:ABC-DEF>> .env
    echo REM TELEGRAM_CHAT_ID=-1001234567890>> .env
    echo.>> .env
    echo # License (required)>> .env
    echo CONTENT_STRATEGIST_LICENSE=your_license_key_here>> .env
    echo.>> .env
    echo # Optional: License server (for custom deployments)>> .env
    echo REM LICENSE_GIST_URL=https://gist.githubusercontent.com/USER/GIST_ID/raw/licenses.json>> .env
    echo REM LICENSE_CACHE_TTL=86400>> .env
    echo REM LICENSE_FAIL_OPEN=false>> .env
    echo ✅ Created .env template — edit it with your keys!
)

REM Create .gitignore
if not exist .gitignore (
    echo # Virtual environment>.gitignore
    echo .venv/>>.gitignore
    echo venv/>>.gitignore
    echo env/>>.gitignore
    echo.>>.gitignore
    echo # Environment files>>.gitignore
    echo .env>>.gitignore
    echo .env.local>>.gitignore
    echo.>>.gitignore
    echo # State ^& runtime>>.gitignore
    echo state/>>.gitignore
    echo output/>>.gitignore
    echo *.log>>.gitignore
    echo.>>.gitignore
    echo # Python>>.gitignore
    echo __pycache__/>>.gitignore
    echo *.pyc>>.gitignore
    echo .pytest_cache/>>.gitignore
    echo .mypy_cache/>>.gitignore
    echo.>>.gitignore
    echo # IDE>>.gitignore
    echo .vscode/>>.gitignore
    echo .idea/>>.gitignore
    echo *.swp>>.gitignore
    echo.>>.gitignore
    echo # OS>>.gitignore
    echo .DS_Store>>.gitignore
    echo Thumbs.db>>.gitignore
    echo.>>.gitignore
    echo # License cache>>.gitignore
    echo ~\.content_strategist\>>.gitignore
)

echo.
echo ✅ Installation complete!
echo.
echo 📋 Next steps:
echo   1. Edit .env with your API keys and license
echo   2. Activate environment: .venv\Scripts\activate
echo   3. Test: python scripts\validate_tone.py config\tone_of_voice.yaml
echo   4. Run pipeline: python scripts\module1_pipeline.py --input transcripts\sample.txt --tone b2b_corporate --platforms instagram,linkedin,twitter,youtube,tiktok_enhanced,threads,newsletter
echo.
echo 📖 Full guide: QUICKSTART.md
echo 📖 License setup: LICENSE_GIST_TEMPLATE.json
echo.
echo 🚀 Ready to create viral content!