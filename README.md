
Description  
  
This project is a Python based Automation tool that provides capabilities of performing certain set of actions to gmail   
account. The project is mainly designed to optimize and efficiently manage their emails by performing costumized actions like   
marking labels, archiving, reading and many more based on specific criteria.  
  
Features  
  
Email Fetcher - Fetch Emails details from gmail account and store them into Database.  
Process Emails - Process the stored Emails from DB based on set actions and rules provided by user through REST API.  
  
How to use -   
  
1) Clone the repository.  
2) Install the dependencies from requirements.txt file  
   - pip install requirements.txt  
3) API Configuration:   
   - Enable the Gmail API in the Google Developers Console.  
   - Download the client configuration and save it as credentials.json in the project directory.  
  
4) Set up a config.ini file and store the path to the client_secret.json and also fill the Database credentials. Refer code to know the actual field names and fill them accordingly  
  
  
Usage -  
  
1) Run the read_emails.py file  
   - Initially there will be a call for gmail authentication, which should be done via default browser. Post verfication - token.pickle file is created which will be used for further access to utilize Gmail APIs.  
     - python3 read_emails.py  
   - Emails are now stored to the table mentioned in the Database.  
2) Run the process_emails.py    
   - This file runs a local Flask service and we can utlilize the "{ip}/process_emails" - endpoint and performs actions based on the payload.    
     - python3 process_emails.py  
  
Configuration -   
  
- A sample file has been added here - "rules_sample.json", this can be utilized to form payload for any type of actions and perform rules on them.  
-  The rules can include conditions based on email attributes like sender, subject, and received date.
