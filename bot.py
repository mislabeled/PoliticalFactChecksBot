'''
Created on Aug 21, 2012
'''

import sys
import re
import urllib2
import reddit
import feedparser
import sqlite3
from BeautifulSoup import BeautifulSoup

SUBREDDIT = 'PoliticalFactChecks'
USERNAME = 'PoliticalFactChecks'
USER_AGENT = 'PoliticalFactChecksBot/0'
POLITIFACT_RSS = 'http://www.politifact.com/feeds/statements/truth-o-meter/'
FACTCHECK_ORG_RSS = 'http://factcheck.org/feed/rss/'
WAPO_FACT_CHECKER_RSS = 'http://feeds.washingtonpost.com/rss/rss_fact-checker'

SOURCE_POLITIFACT = 'Politifact'
SOURCE_FACTCHECK_ORG = 'FactCheck.org'
SOURCE_WAPO = 'WaPo'

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
    
    def get_url(self):
        return self.url
    
    def get_guid(self):
        return self.guid

    def get_title(self):
        verdict = self.get_verdict()
        if verdict == None:
            return "[%s] %s" % (self.source_name, self._get_clean_title())
        return "[%s] %s [%s]" % (self.source_name, self._get_clean_title(), verdict)
    
    def get_text(self):
        return "%s\n\n%s" % (self._get_clean_text(), self.get_link())
    
    def get_link(self):
        return '[Read More](%s)' % self.link

    def _get_clean_title(self):
        return ''.join(BeautifulSoup(self.title).findAll(text=True)).replace('&quot;', '"').replace('&rsquo;', "'").replace('&lsquo;', "'").replace('&hellip;', '...').replace('\n', '').replace('\t', '').replace('&nbsp;', ' ')
        
    def _get_clean_text(self):
        return ''.join(BeautifulSoup(self.description).findAll(text=True)).replace('... >> More', '').replace('&#8230; More >>', '').replace('Read full article  &gt;&gt;', '').replace('&amp;', '&')
    
    def get_verdict(self):
        return None

class PolitifactSubmission(Submission):
    def __init__(self, url, guid, title, link, description):
        Submission.__init__(self, SOURCE_POLITIFACT, url, guid, title, link, description)
    
    def get_verdict(self):
        """ read first few words from description: 'The Truth-o-Meter says: Half-True' """
        if self.description.startswith('The Truth-o-Meter says:'):
            desc_split = self.description.split('|')
            if len(desc_split) > 0:
                return desc_split[0].replace('The Truth-o-Meter says:', '').strip()
        return None

class FactcheckOrgSubmission(Submission):
    def __init__(self, url, guid, title, link, description):
        Submission.__init__(self, SOURCE_FACTCHECK_ORG, url, guid, title, link, description)
    
    def get_verdict(self):
        # TODO: looking for some consistent scheme
        return None

class WashingtonPostSubmission(Submission):
    def __init__(self, url, guid, title, link, description):
        Submission.__init__(self, SOURCE_WAPO, url, guid, title, link, description)
    
    def get_verdict(self):
        """ look for images on full page: pinocchio_1.jpg, pinocchio_2.jpg, pinocchio_3.jpg, or pinocchio_4.jpg """
        soup = BeautifulSoup(urllib2.urlopen(self.link))
        image_src_list = [image['src'] for image in soup.findAll('img', attrs={'src' : re.compile('pinocchio_(\d)\.jpg')})]
        verdicts = [self._get_pinocchio_text(re.search('pinocchio_(\d)\.jpg', img_src).group(1)) for img_src in image_src_list]
        if len(verdicts) > 0:
            return ', '.join(verdicts)
        return None
    
    def _get_pinocchio_text(self, nose_count):
        if nose_count == '1':
            return '%s Pinocchio' % nose_count
        return '%s Pinocchios' % nose_count
        

#### database methods ####
def already_been_posted(url, guid):
    c.execute('select id from submission where url = ? and guid = ? limit 1', (url, guid))
    result = c.fetchone()
    if result != None and result[0] > 0:
        return True
    return False

def set_posted(url, guid):
    c.execute("insert into submission(url, guid) values ('%s', '%s')" % (url, guid))
    conn.commit()
   

#### feed/submission methods ####
def get_feed_entries(url):
    return feedparser.parse(url).entries

def get_submissions(clazz, url):
    return [clazz(url, entry['guid'], entry['title'], entry['link'], entry['description']) for entry in get_feed_entries(url) if not already_been_posted(url, entry['guid'])]

def get_politifact_submissions():
    return get_submissions(PolitifactSubmission, POLITIFACT_RSS)

def get_factcheckorg_submissions():
    return get_submissions(FactcheckOrgSubmission, FACTCHECK_ORG_RSS)

def get_wapofactchecker_submissions():
    return get_submissions(WashingtonPostSubmission, WAPO_FACT_CHECKER_RSS)


def read_password_from_file():
    return open('password.txt').read()
    
def main():    
    submissions = []
    submissions.extend(get_politifact_submissions())
    submissions.extend(get_factcheckorg_submissions())
    submissions.extend(get_wapofactchecker_submissions())
    
    if len(submissions) > 0:
        r = reddit.Reddit(user_agent=USER_AGENT)
        r.login(USERNAME, read_password_from_file())
        
        for submission in submissions:
            print "submitting %s" % submission.get_guid()
            r.submit(SUBREDDIT, submission.get_title(), submission.get_text())
            set_posted(submission.get_url(), submission.get_guid())

    return 0

if __name__ == '__main__':
    sys.exit(main())