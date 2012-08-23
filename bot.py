'''
Created on Aug 21, 2012
'''

import reddit
import feedparser
import sqlite3
from BeautifulSoup import BeautifulSoup

SUBREDDIT = 'PoliticalFactChecks'
USERNAME = 'PoliticalFactChecks'
PASSWORD = 'notreallythepassword'
USER_AGENT = 'PoliticalFactChecksBot/0'
TRUTH_O_METER_RSS = 'http://www.politifact.com/feeds/statements/truth-o-meter/'
FACT_CHECK_ORG_RSS = 'http://factcheck.org/feed/rss/'
WAPO_FACT_CHECKER = 'http://feeds.washingtonpost.com/rss/rss_fact-checker'

conn = sqlite3.connect('db/PoliticalFactChecks.db')
c = conn.cursor()

class Submission:
    def __init__(self, source_name, url, guid, title, link, description):
        self.source_name = source_name
        self.url = url
        self.guid = guid
        self.title = title
        self.link = link
        self.description = description

    def get_source_name(self):
        return self.source_name

    def get_title(self):
        clean_title = self.title.replace('&quot;', '"')
        clean_title = clean_title.replace('\n', '')
        clean_title = clean_title.replace('\t', '')
        return "[%s] %s" % (self.source_name, clean_title)
    
    def get_text(self):
        return "%s\n\n%s" % (_clean_tags(self.description), self.get_link())
    
    def get_link(self):
        return '[Read More](%s)' % self.link

def _clean_tags(code):
    # TODO: clean HTML entities
    return ''.join(BeautifulSoup(code).findAll(text=True)).replace('... >> More', '').replace('&#8230; More >>', '')
    
def already_been_posted(url, guid):
    c.execute('select id from submission where url = ? and guid = ? limit 1', (url, guid))
    result = c.fetchone()
    if result != None and result[0] > 0:
        return True
    c.execute("insert into submission(url, guid) values ('%s', '%s')" % (url, guid))
    conn.commit()
    return False

def get_submissions(source_name, url):
    submissions = []
    truth_o_meter_feed = feedparser.parse(url)
    for entry in truth_o_meter_feed.entries:
        guid = entry['guid']
        title = entry['title']
        link = entry['link']
        description = entry['description']
        if not already_been_posted(url, guid):
            submissions.append(Submission(source_name, url, guid, title, link, description))
    return submissions
            

def get_politifact_submissions():
    return get_submissions("Politifact", TRUTH_O_METER_RSS)

def get_factcheckorg_submissions():
    return get_submissions("FactCheck.org", FACT_CHECK_ORG_RSS)

def get_wapofactchecker_submissions():
    return get_submissions("WaPo", WAPO_FACT_CHECKER)

def run():
    r = reddit.Reddit(user_agent=USER_AGENT)
    r.login(USERNAME, PASSWORD)
    
    submissions = []
    submissions.extend(get_politifact_submissions())
    submissions.extend(get_factcheckorg_submissions())
    #submissions.extend(get_wapofactchecker_submissions())
    
    for submission in submissions:
        r.submit(SUBREDDIT, submission.get_title(), submission.get_text())

if __name__ == '__main__':
    run()