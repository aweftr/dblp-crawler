# %%
import requests
from bs4 import BeautifulSoup
import re
import csv
import logging
import argparse
import pandas as pd
import os

# %%
parser = argparse.ArgumentParser(description='dblp paper crawler.')
parser.add_argument("--filename", default="data.csv", metavar="*.csv", 
    help="filename to save the papers. default: data.csv")
parser.add_argument("--loglevel", choices=["debug", "info", "silent"], default="debug", 
    help="logging level. defaule: silent")
parser.add_argument("--logfilename", default="searchPaper.log")
args = parser.parse_args()

# %%
logmap = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "silent": logging.CRITICAL
}
logger = logging.getLogger("dblp paper search log")
logger.setLevel(logmap[args.loglevel])
# logging File handler
ch = logging.FileHandler(args.logfilename, "w")
ch.setLevel(logmap[args.loglevel])
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
# logging stream handler
sh = logging.StreamHandler()
sh.setLevel(logmap[args.loglevel])
shf = logging.Formatter("%(message)s")

logger.addHandler(ch)
logger.addHandler(sh)

# %%
class Paper():
    def __init__(self, title=None, url=None):
        self.title = title
        self.url = url
        self.authors = []
    
    def __str__(self) -> str:
        assert self.title is not None
        return self.title
    
    def __repr__(self) -> str:
        assert self.title is not None
        return self.title

def savePaper2csv(paper_list, filename):
    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["title", "authors", "url"])
        for paper in paper_list:
            writer.writerow([paper.title, ", ".join(i for i in paper.authors), paper.url])


def getContentStrings(tag):
    tmp = ""
    for c in tag.contents:
        clen = 0
        try:
            clen = len(c.contents)
        except AttributeError:
            clen = 0
        if clen:
            cstr = getContentStrings(c)
            tmp += cstr
        else:
            tmp += c.string
    return tmp

# %%
dblp_url = "https://dblp.org/search/publ/inc"
logger.debug("dblp url: {}".format(dblp_url))
paper_list = []

# You should modify the following two lines to include your own paper list!
df = pd.read_excel("survey.xlsx")
mydf = df[df["负责人"] == "程云龙"]["title"]
try:
    for papername in mydf:
        payload = {
            "q": papername,
            "s": "ydvspc",
            "h": "1000",
            "b": "0",
        }
        logger.debug("url payload: {}".format(payload))
        r = requests.get(dblp_url, params=payload)
        logger.debug(r.url)
        soup = BeautifulSoup(r.text, "html.parser")
        record_list = soup.find_all("li", class_=re.compile("inproceedings|article"))
        logger.debug("Start processing response.")
        if len(record_list) == 0:
            logger.warning("No more paper can be found!")
        elif len(record_list) != 1:
            logger.warning("More than one paper are found!")
        logger.debug("find {} records".format(len(record_list)))
        for idx, record in enumerate(record_list):
            authors = record.cite.find_all(itemprop="author")
            title_tag = record.cite.find(class_="title")
            paper_title = getContentStrings(title_tag)
            if papername.lower() not in paper_title.lower():
                logger.error("{} not in {}".format(papername, paper_title))
                continue
            try:
                paper_url = record.nav.ul.li.div.a["href"]
            except:
                paper_url = None
                logger.error("Cannot find the url of this paper. Use None instead.")
            
            pp = Paper(title=paper_title, url=paper_url)
            for author in authors:
                pp.authors.append(author.a.string)
            paper_list.append(pp)
except Exception as e:
    logger.error("There is an exception!" + e)
# %%
if len(paper_list):
    savePaper2csv(paper_list, args.filename)
    logger.info("paper list saved to {}".format(args.filename))
