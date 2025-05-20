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
- [ ] Read keywords from a json file
- [ ] More

### New crawler features
No more python crawler. Use the sparql query instead. Fast and accurate!
- [x] Search by title regex for any publication types (conferences, journals, etc.)
  - [x] Keywords separated by spaces must all appear somewhere in the title.
  - [x] Keywords joined by '|' act as an OR condition in the title match.
- [x] Select author, conference, year and doi by your will.
- [x] Filter publications by year (greater equal).
- [x] Remember past search query and load it. 
- [x] Show results in a scrollable manner. 
- [x] Save query results to user specified filename. 
- [x] Clear all selected conferences with one click. 
- [x] Accurate search (conference name must equal to the given name without workshop or other prefix and suffix) and fuzzy search (prefix and suffix in conference name is allowed) for conference. 

### Things to be implemented
- [ ] Add journal selection
- [ ] Filter workshop contents
- [ ] Read keywords from a json file
- [ ] More