"""
Configuration of 'memos' Flask app. 
Edit to fit development or deployment environment.

"""
import random 

### My local development environment
#PORT=5000
#DEBUG = True
#MONGO_URL = "mongodb://memo:iremember@localhost:27333/memos"  # on Gnat

### On ix.cs.uoregon.edu (Michal Young's instance of MongoDB)
PORT=random.randint(5000,8000)
DEBUG = False # Because it's unsafe to run outside localhost
MONGO_URL =  "mongodb://memo:mongo@ix.cs.uoregon.edu:4260/memos"  # on ix
