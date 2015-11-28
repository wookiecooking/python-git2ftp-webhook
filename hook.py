import os
from sys import platform as _platform
from flask import Flask
from flask import request
app = Flask(__name__)
from ftplib import FTP
from git import *

FTP_ADDRESS = os.environ['FTP_ADDRESS'] # ftp.example.com
FTP_USER = os.environ['FTP_USER'] # ftp user
FTP_PASSWORD = os.environ['FTP_PASS'] # ftp password
FTP_ROOT_DIR = os.environ['FTP_DIR'] # /path/to/where/repo/should/go
REPO_ROOT = os.environ['REPO_DIR'] # /path/to/some/repo
WEBHOOK_PORT = os.environ['WEBHOOK_PORT'] # 5000
WEBHOOK_HOST = os.environ['WEBHOOK_HOST'] # '0.0.0.0'


###############################################################################
# SECTION: Private methods
###############################################################################
def _connectToFTP(host, user, password):
   print green("** Connecting to the server **")
   ftp = FTP(host=host, user=user, passwd=password)
   return ftp

def _gitLatestFiles():
   print "** Connecting to Git **"

   g = Git(REPO_ROOT)
   repo = Repo(REPO_ROOT)
   headCommit = repo.head.commit

   print "Head commit revision: %s" % headCommit
   print "Message: %s" % headCommit.message

   result = g.execute(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", str(headCommit)])
   files = result.split("\n")

   return files


###############################################################################
# SECTION: Actions
###############################################################################

def uploadLatest():
   print ""
   print "** Upload latest changes **"

   ftp = _connectToFTP(FTP_ADDRESS, FTP_USER, FTP_PASSWORD)
   files = _gitLatestFiles()

   for f in files:
      print "Uploading file %s" % f
      split = os.path.split(f)

      ftp.cwd(os.path.join(FTP_ROOT_DIR, split[0]))
      ftp.storlines("STOR %s" % split[1], open(os.path.join("../", f), "r"))

   ftp.quit()

###############################################################################
# SECTION: WebHook
###############################################################################

def displayHTML():
  return 'No hook for you!'

@app.route('/', methods=['GET'])
def index():
    return displayHTML()

@app.route('/webhook', methods=['POST'])
def tracking():
  if request.method == 'POST':
    data = request.get_json()
    repo = data['repository']['name']
    commit_author = data['actor']['username']
    commit_hash = data['push']['changes'][0]['new']['target']['hash'][:7]
    commit_url = data['push']['changes'][0]['new']['target']['links']['html']['href']
    print 'Webhook received! %s committed %s to %s' % (commit_author, commit_hash, repo)
    uploadLatest()
    return '200'
  else:
      return displayHTML()

if __name__ == '__main__':
  app.run(host=WEBHOOK_HOST, port=WEBHOOK_PORT, debug=True)