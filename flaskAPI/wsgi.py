from app import app
import os

sec = os.environ['GOOGLE_CRED']
with open('json_cred.json', 'w') as outfile:
    outfile.write(sec)

if __name__ == "__main__":
    app.run()
