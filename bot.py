'''
Created on Aug 21, 2012
'''

import reddit
import feedparser

SUBREDDIT = 'PoliticalFactChecks'
USERNAME = 'PoliticalFactChecks'
PASSWORD = 'notreallythepassword'
USER_AGENT = 'PoliticalFactChecksBot/0'
TRUTH_O_METER_RSS = 'http://www.politifact.com/feeds/articles/truth-o-meter/'
FACT_CHECK_ORG_RSS = 'http://factcheck.org/feed/rss/'
WAPO_FACT_CHECKER = 'http://feeds.washingtonpost.com/rss/rss_fact-checker'

class Submission:
    def __init__(self, source, guid, title, link, description):
        self.source = source
        self.guid = guid
        self.title = title
        self.link = link
        self.description = description

    def get_title(self):
        return "[%s] %s" % (self.source, self.title)
    
    def get_text(self):
        return self.description
        

def already_been_posted(source, guid):
    # TODO: implement this
    return False

def get_submissions(source, url):
    submissions = []
    truth_o_meter_feed = feedparser.parse(url)
    for entry in truth_o_meter_feed.entries:
        guid = entry['guid']
        title = entry['title']
        link = entry['link']
        description = entry['description']
        if not already_been_posted(url, guid):
            submissions.append(Submission(source, guid, title, link, description))
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