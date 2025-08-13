# 📈 AlphaNiftyAI – LLM-powered Stock Market Strategy Backtesting

MarketSenseAI is a research framework that uses **Large Language Models (LLMs)** to process **price trends, fundamentals, news sentiment, and macroeconomic factors** to generate **BUY/SELL/HOLD** trading signals — and then backtests multiple portfolio strategies.

---

## 🚀 Features
- **Signal Generation**
  - Monthly & Weekly LLM-based signals
  - Confidence scores from LLaMA3-70B via **Groq API**
- **Strategies Implemented**
  - MS (MarketSenseAI Equal Weight)
  - MS-L (Buy-only Equal Weight)
  - MS-L-Cap (Buy-only Market Cap Weighted)
  - MS-TopN-GPT
  - MS-High-GPT / MS-Low-GPT
  - MS-TopN-Cap-GPT
  - NIFTY++
- **Backtesting**
  - Calculates returns, Sharpe Ratio, Sortino Ratio, Max Drawdown, Win Rate
  - Benchmark comparison with NSEI
- **Data Handling**
  - Uses monthly/weekly price data from `data/prices/`
  - Market Cap data from `data/market_cap/`
  - Summaries from `results/summaries_*`
- **Supports Multiple GROQ API Keys**
  - Automatic rotation on quota limit

---



# Guide for runnig the project:
Requirements-
- Python should be installed (https://www.python.org/downloads/).
- Also make sure you have VS code installed for viewing the code. Step by step guide to download VS code can be found on https://code.visualstudio.com/download

  Prerequisites for setting up the project: Git, Python (3.8+)


Python: https://www.python.org/downloads/
Git: https://git-scm.com/downloads/win

Windows:

Also make sure you have VS Code installed, for viewing the code. For a step by step guide on how to install VS Code visit https://code.visualstudio.com/docs/setup/windows

For a step step guide on how to install git, visit 
Git Link: https://git-scm.com/downloads/win
https://phoenixnap.com/kb/how-to-install-git-windows

For a step by step guide on how to install python, refer to 
Link:https://www.python.org/downloads/
https://phoenixnap.com/kb/how-to-install-python-3-windows




Python and pip installation can be verified using,

python/python3 –version
pip/pip3 –version




For Linux OS (to install all prerequisites):

# Update and upgrade system packages
sudo apt update && sudo apt upgrade -y

# Install Git
sudo apt install git -y
git --version

# Install Python 3 and pip
sudo apt install python3 python3-pip -y
python3 --version
pip3 --version
sudo apt install python3.8 -y




—----------------------------------------------------------------------------------------------------------------------------
After installing the required packages, next download the code from gitHub repository


    1. Open Terminal

    2. git clone https://github.com/mayurg33/AlphaNiftyAI.git

    3. cd AlphaNiftyAI-master

    4. git checkout master

Running the code:

    1. pip install virtualenv (only first time)
    2. virtualenv venv (Creates a Virtual Environment) (only first time)
    3. “venv\Scripts\activate” (Activate the virtual environment) on Windows and “source venv/bin/activate” on Linux based OS.
    4. In case Windows shows that scripts aren’t permitted to run by this user, run the following command:

		Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUse		
    5. pip install -r "requirements.txt"
    6. If installing from requirements.txt causes any issue then, then run 
	
     pip install beautifulsoup4==4.13.4 dotenv faiss-cpu groq bnumpy openai orjson pandas playwright plotly 
     python-dotenv simplejson tqdm==4.67.1 vectorbt virtualenv yfinance==0.2.61
then run 
     playwright install
			
    7. Now we have to create an .env file, which we can do in VS Code.
    8. Run “code .” to open the ./backend folder in VS Code and then create a .env file in this folder
    9. If VS Code isn’t available, or if running on a linux based VM, use “nano .env” to create the environment variable file
    10. Add these as env variables


GROQ_API_KEY=\


To make a Groq api key, visit https://console.groq.com/keys \
now open the project folder in vs code \
Though all the data is already fetch and is in the data folder yet if want to fetch then read below instructions:\
      **For fetching the monthly data go inside the monthly_llama70b folder and run : **\
     **Fundamentals data**-\
     fetch_fundamentals_loop.py\
     **Stock price data**-\
 	 fetch_price_by_month.py\
     **News-**\
	 fetch_news_playwright_loop.py\
     -Microeconomic data was manually fetched fron NSE and worldbank website\
	 **generating peer map-**\
      generate_peer_map.py\
  **for summarising:**\
   **fundamentals data:**\
   open summarixe_fundamentals_loop.py\
   paste the groq api key in client = Groq(api_key="")\
    run summarixe_fundamentals_loop.py\
   **News:**\
   open summarize_news_loop.py\
   paste the groq api key in client = Groq(api_key="")\
    run summarize_news_loop.py\
   **stock data:**\
    open summarize_price_loop.py\
    paste the groq api key in client = Groq(api_key="")\
     run summarize_price_loop.py\\

   micro economic data was summarized manually but it is in data folder\
    **For final signal genration-**\
	 run genrate_signal_confidence.py\
  
 # Evaluation for monthly strategies
 Run All the files Sarting with "MS"


 # Weekly signals
 1. Data Fetching:\
    Data is already fetched but you can run the scripts using vs code inside the src/weekly_llama70b:\
    fetch_news_weekly.py\
    fetch_weekly_fundamentals.py\
    fetch_weekly_prices.py\
    same microeconomic data was used as in monhly data. \
 3. Summarizing:\
      Though all the summaries are arleady done , if you want you can run\
      summarize_fundamental_weekly.py\
      summarize_news_weekly.py\
      summarize_price_weekly.py\
      summary_macro.py\
 3.Signal generation run\
    generate_signals_weekly.py\

# Evaluation for weeekly signals strategies
  Run all the files starting with MS and additionally run nifyplusplus.py and topN-cap-GPT-NIFTYpp.py
    
       
    

 
 

																										
