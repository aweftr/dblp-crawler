## dblp crawler

### Install python environment

Use `poetry install --only main` to install python requirements. 

### Features

Crawl papers for specific conferences in dblp with multiple keywords. 

- [x] Crawl conference
- [x] Simple regex to filter workshop or other session
- [x] Log to a file and stream to console

### Usage

`poetry shell` to use the created python virtual environment. 

`python mydblp.py -h` for the help message. 

`python mydblp.py --conf="sc"` to crawl a specific conference. 


### Things to be implemented
- [ ] Crawl journal
- [ ] Multi-processing crawl
- [ ] Add more regex filters
- [ ] More