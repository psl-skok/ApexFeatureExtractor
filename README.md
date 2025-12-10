# CallTranscriptAnalysis

1. Navigate to root directory
2. Create virtual environment:
    python -m venv .venv
3. Activate the Virtual Environment
    .venv\Scripts\activate
4. Install requirements
     pip install -r requirements.txt
5. To start server run in root directory:
    uvicorn LangChain_Orchestration.server.main:app --reload

6. To test server, run in root directory:
python LangChain_Orchestration\server\test_api.py



# Running the Front End

1. Navigate to the front_end folder
2. Install dependences with "npm install" (only needed the first time)
2. Start the development server with "npm run dev"
3. Visit http://localhost:3000 in your browser

Testing editing the repo
