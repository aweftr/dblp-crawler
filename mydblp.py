# %%
import requests
from bs4 import BeautifulSoup
import re
import csv
import logging
import argparse
import os

# %%
parser = argparse.ArgumentParser(description='dblp paper crawler.')
parser.add_argument('--syear', type=int, default=2018, metavar="INT", 
                    help='year to start the crawler. default: 2018')
parser.add_argument("--sthreshod", type=float, default=0.4, metavar="FLOAT", 
    help="threshod for the paper score to add to paper list. default: 0.4")
parser.add_argument("--filename", default="data.csv", metavar="*.csv", 
    help="filename to save the papers. default: data.csv")
parser.add_argument("--strictmatch", type=bool, default=False, 
    help="enable conference strict match, e.g., do not match workshop. default: False")
parser.add_argument("--conf", default=None, 
    help='''
    choice one from the following conference. default: None (search all conferences)
    "ARCH": ["hpca", "micro", "sc", "asplos", "isca", "usenix", "eurosys", "socc", "spaa", "cluster", "icdcs", "sigmetrics", "icpp", "ipps", "performance", "hpdc", "europar"], 
    "NET": ["infocom", "iwqos"], 
    "SOFT": ["sosp", "osdi", "icsoc", "icws", "middleware"], 
    "DM": ["sigmod", "kdd", "icde", "cikm", "wsdm", "dasfaa", "pkdd", "iswc", "icdm", "cidr"], 
    "AI":["aaai", "nips", "icml", "ijcai", "iclr"]
    Notes: ipps means IPDPS.
    ''')
parser.add_argument("--loglevel", choices=["debug", "info", "silent"], default="info", 
    help="logging level. defaule: silent")
parser.add_argument("--logfilename", default="dblplog.log")
args = parser.parse_args()

# %%
logmap = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "silent": logging.CRITICAL
}
logger = logging.getLogger("dblp crawler log")
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
# keywords = {
#     "virtual": 0.2,
#     "machine": 0.2,
#     "vm": 0.2,
#     "task": 0.2,
#     "job": 0.2,
#     "server": 0.2,
#     "cloud": 0.3,
#     "placement": 0.2,
#     "center": 0.2,
#     "data": 0.2,
#     "workload": 0.2,
#     "interference": 0.4,
#     "contention": 0.3,
#     "schedul": 0.4,
#     "qos": 0.4,
#     "utilization": 0.2,
#     "locat": 0.2,
#     "colocation": 0.2,
#     "share": 0.2,
#     "consolidat": 0.2,
#     "heterogene": 0.2,
#     "resource": 0.3,
#     "efficien": 0.2,
#     "predict": 0.3,
#     "perform": 0.2,
#     "degrad": 0.2,
#     "service": 0.2,
#     "sensi": 0.2,
#     "chance": 0.3,
#     "noise": 0.3,
#     "imbalanc": 0.3,
#     "time": 0.3,
#     "series": 0.2,
#     "classification": 0.2,
#     "forecasting": 0.2,
#     "cold": 0.3,
#     "start": 0.2,
#     "anomaly": 0.2,
#     "deploy": 0.2,
#     "allot": 0.2,
#     "performance": 0.2
# }

keywords = {
    "virtual": 0.2,
    "machine": 0.2,
    "vm": 0.2
}

venue_set = {
    "ARCH": ["hpca", "micro", "sc", "asplos", "isca", "usenix", "eurosys", "socc", "spaa", "cluster", "icdcs", "sigmetrics", "icpp", "ipps", "performance", "hpdc", "europar"], 
    "NET": ["infocom", "iwqos"], 
    "SOFT": ["sosp", "osdi", "icsoc", "icws", "middleware"], 
    "DM": ["sigmod", "kdd", "icde", "cikm", "wsdm", "dasfaa", "pkdd", "iswc", "icdm", "cidr"], 
    "AI":["aaai", "nips", "icml", "ijcai", "iclr"]
}

YEAR_START = args.syear
SCORE_THRESHOD = 0.4
# %%
class Paper():
    def __init__(self, title=None, venue=None, year=None, pages=None):
        self.title = title
        self.venue = venue
        self.year = year
        self.pages = pages
        self.authors = []
        self.score = None

    def calScore(self):
        s = 0.
        for keyword in keywords:
            if keyword in self.title.lower():
                s += keywords[keyword]
        self.score = s

    def __str__(self):
        assert self.title is not None
        assert self.venue is not None
        assert self.year is not None
        return "{} {}, {} {}".format(self.title, self.pages, self.venue, self.year)

def savePaper2csv(paper_list, filename):
    with open("{}".format(filename), "w") as f:
        writer = csv.writer(f)
        writer.writerow(["title", "venue", "year", "pages", "authors"])
        for paper in paper_list:
            writer.writerow([paper.title, paper.venue, paper.year, paper.pages, ", ".join(i for i in paper.authors)])


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

def searchConference(conf, keywords):
    dblp_url = "https://dblp.org/search/publ/inc"
    # conf = "aaai"
    confre = re.compile(conf, re.IGNORECASE)
    if args.strictmatch:
        confre = re.compile("(?=^((?!workshop).)*$)(?=[^@]?{}[^@]?)".format(conf), re.IGNORECASE)
    logger.debug(args.strictmatch)
    logger.debug(confre)

    search_word = "|".join(i for i in keywords)
    search_word += " streamid:conf/{}:".format(conf)

    page = 0
    year = 0
    year_smaller_bool = False
    paper_list = []
    while True:
        payload = {
                "q": search_word,
                "s": "ydvspc",
                "h": "1000",
                "b": "{}".format(page),
            }
        logger.debug("dblp url: {}".format(dblp_url))
        logger.debug("url payload: {}".format(payload))
        r = requests.get(dblp_url, params=payload)
        logger.debug(r.url)
        logger.info("Request {} 1000 records the {} time".format(conf, page+1))
        soup = BeautifulSoup(r.text, "html.parser")
        record_list = soup.find_all("li", class_=re.compile("year|inproceedings"))
        logger.debug("Start processing response.")
        if len(record_list) == 0:
            logger.warning("No more paper can be found!")
            break
        for idx, record in enumerate(record_list):
            if "year" in record["class"]:
                year = int(record.string)
                logger.debug("Find year record {}.".format(year))
                if year < YEAR_START:
                    year_smaller_bool = True
                    logger.info("Current year smaller than YEAR_START! Finish finding paper list.")
                    break
                continue
            if "inproceedings" not in record["class"]:
                logger.debug("No inproceedings in record class: {}".format(record["class"]))
                # print("This is not a conference paper!")
                continue
            # try:
            authors = record.cite.find_all(itemprop="author")
            title_tag = record.cite.find(class_="title")
            paper_title = getContentStrings(title_tag)
            paper_venue = record.cite.find(itemprop="isPartOf").string
            if not re.match(confre, paper_venue):
                logger.warning("Ignore {}".format(paper_venue))
                continue
            paper_pagination = record.cite.find(itemprop="pagination")
            if paper_pagination:
                paper_pagination = paper_pagination.string
            else:
                logger.warning("Paper with no pagination. venue: {}".format(paper_venue))
            
            # except AttributeError as err:
            #     print(err)
            #     print("\tidx: {}, venue: {}".format(idx, paper_venue))
            #     # continue
            pp = Paper(title=paper_title, venue=paper_venue, year=year, pages=paper_pagination)
            for author in authors:
                pp.authors.append(author.a.string)
            pp.calScore()
            
            if pp.score >= SCORE_THRESHOD:
                paper_list.append(pp)
                logger.debug("title: {}, venue: {}, year: {}, pages: {}".format(pp.title, pp.venue, pp.year, pp.pages))
        if year_smaller_bool:
            break

    logger.info("Find {} papers".format(len(paper_list)))
    return paper_list


if __name__ == "__main__":
    if args.conf:
        conf = args.conf
    logger.info(args)
    paper_list = searchConference(conf, keywords)
    if len(paper_list):
        savePaper2csv(paper_list, args.filename)
        logger.info("paper list saved to {}".format(args.filename))

