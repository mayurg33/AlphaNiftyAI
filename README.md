**Guide for runnig the project:**
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
	
pip install beautifulsoup4==4.13.4 dotenv faiss-cpu groq bnumpy openai orjson pandas playwright plotly python-dotenv simplejson tqdm==4.67.1 vectorbt virtualenv yfinance==0.2.61
then run 
 playwright install
			
    7. Now we have to create an .env file, which we can do in VS Code.
    8. Run “code .” to open the ./backend folder in VS Code and then create a .env file in this folder
    9. If VS Code isn’t available, or if running on a linux based VM, use “nano .env” to create the environment variable file
    10. Add these as env variables


GROQ_API_KEY=


To make a Groq api key, visit https://console.groq.com/keys


