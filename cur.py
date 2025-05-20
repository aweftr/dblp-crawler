# %%
import urwid
import math
import pandas as pd
import json
from SPARQLWrapper import SPARQLWrapper, JSON

sparql = SPARQLWrapper(
    "https://sparql.dblp.org/sparql"
)
sparql.setReturnFormat(JSON)

# Input widgets
total_checkboxes = []
name_edit = urwid.Edit("Search Name: ")
fuzzy_checkbox = urwid.CheckBox("with fuzzy search (default accurate search)", state=False)
year_checkbox = urwid.CheckBox("Filter by year", state=False)
year_edit = urwid.Edit("Year >= than: ")
year_edit_wrap = urwid.AttrMap(year_edit, 'default')
query_text = urwid.Text("")
total_checkboxes.extend([fuzzy_checkbox, year_checkbox])

isQueried = False
# Conference names
# conf_names = [
#     "hpca", "micro", "sc", "asplos", "isca", "usenix", "eurosys", "socc",
#     "spaa", "cluster", "icdcs", "sigmetrics", "icpp", "ipps", "performance", "hpdc", "europar"
# ]
conf_names = {
    "ARCH": ["hpca", "micro", "sc", "asplos", "isca", "usenix", "eurosys", "socc", "spaa", "cluster", "icdcs", "sigmetrics", "icpp", "ipps", "performance", "hpdc", "europar"], 
    "NET": ["infocom", "iwqos"], 
    "SOFT": ["sosp", "osdi", "icsoc", "icws", "middleware"], 
    "DM": ["sigmod", "kdd", "icde", "cikm", "wsdm", "dasfaa", "pkdd", "iswc", "icdm", "cidr"], 
    "AI":["aaai", "nips|neurips", "icml", "ijcai", "iclr"]
}

select_names = ["authors", "conference", "year", "doi"]
# conf_checkboxes = [urwid.CheckBox(conf) for conf in conf_names]

# Arrange checkboxes into 3 columns
def build_checkbox_grid(checkboxes, num_cols=3):
    num_rows = math.ceil(len(checkboxes) / num_cols)
    grid = []
    for row_idx in range(num_rows):
        row_items = []
        for col_idx in range(num_cols):
            idx = col_idx + row_idx * num_cols
            if idx < len(checkboxes):
                row_items.append(urwid.AttrMap(checkboxes[idx], None))
            else:
                row_items.append(urwid.Text(""))  # Empty cell
        grid.append(urwid.Columns(row_items, dividechars=2))
    return grid

def build_conf_types(conf_names, num_cols=4):
    grids = []
    conf_checkboxes = []
    grids.append(urwid.Columns([urwid.Text("Select Conferences"), fuzzy_checkbox]))
    for conf_type in conf_names:
        grids.append(urwid.Text(conf_type))
        conf_checkboxes_tmp = [urwid.CheckBox(conf) for conf in conf_names[conf_type]]
        conf_checkboxes.extend(conf_checkboxes_tmp)
        grid = build_checkbox_grid(conf_checkboxes_tmp, num_cols)
        grids.extend(grid)
    return grids, conf_checkboxes

conf_grid_rows, conf_checkboxes = build_conf_types(conf_names, 4)
select_checkboxes = [urwid.CheckBox(sname) for sname in select_names]
select_grid_rows = build_checkbox_grid(select_checkboxes, 4)
total_checkboxes.extend(conf_checkboxes)
total_checkboxes.extend(select_checkboxes)

def on_clear_clicked(button):
    for cb in conf_checkboxes:
        cb.set_state(False)

clear_conf_button = urwid.Button("Clear Selected Conf", align="center")
urwid.connect_signal(clear_conf_button, 'click', on_clear_clicked)


class SearchQuery:
    def __init__(self):
        self.name = None
        self.checkedboxes = []
        self.year = None
    
    def getState(self):
        self.name = name_edit.edit_text.strip()
        for cb in total_checkboxes:
            if cb.get_state():
                self.checkedboxes.append(cb.get_label())
        if year_checkbox.get_state():
            self.year = year_edit.edit_text.strip()
    
    def to_dict(self):
        return {
            "name": self.name,
            "checkedboxes": self.checkedboxes,
            "year": self.year
        }

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)
    
    def loadState(self):
        name_edit.edit_text = self.name
        for cb in total_checkboxes:
            if cb.get_label() in self.checkedboxes:
                cb.set_state(True)
        if self.year:
            year_checkbox.set_state(True)
            year_edit.edit_text = self.year
        else:
            year_checkbox.set_state(False)
            year_edit.edit_text = ""

    def load_from_file(self, filepath):
        """Load query state from a JSON file and apply it to widgets."""
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            self.name = data.get("name")
            self.checkedboxes = data.get("checkedboxes", [])
            self.year = data.get("year")
            self.loadState()
        except Exception as e:
            result_walker.clear()
            result_walker.append(urwid.Text(e))

    
def format_output(ret):
    header = ret["head"]["vars"]
    result = []
    for i in ret["results"]["bindings"]:
        item = []
        for h in header:
            item.append(i[h]["value"])
        result.append(item)
    return header, result

def make_row(cells, is_header=False):
    cols = []
    for cell in cells:
        text = urwid.Text(cell, align='left')
        if is_header:
            text = urwid.AttrMap(text, 'header')
        cols.append(('weight', 1, text))
    return urwid.Columns(cols, dividechars=2)

def make_rows(ret):
    header, result = format_output(ret)
    widgets = [make_row(header, is_header=True), urwid.Divider('-')]
    for row in result:
        widgets.append(make_row(row))
        widgets.append(urwid.Divider())
    return widgets

# print(conf_grid_rows)
# %%
# SQL generation logic
def on_generate_clicked(button):
    result_walker.clear()
    result_walker.append(urwid.Text("Querying! Please wait"))
    keywords = name_edit.edit_text.strip().split()
    selected_confs = [cb.label for cb in conf_checkboxes if cb.get_state()]
    selected_variable = [cb.label for cb in select_checkboxes if cb.get_state()]
    if len(selected_variable) == 0:
        result_walker.clear()
        result_walker.append(urwid.Text("Please select something (author, conference...) to query!"))
        return
    selected_variable_str = ""
    select_constraints = ""
    group_constraints = ""
    author_select = False
    for keyword in keywords:
        select_constraints += f'FILTER regex(?title, "{keyword}", "i")\n'
    if "authors" in selected_variable:
        select_constraints += f"""?publ dblp:createdBy ?author .\n?author rdfs:label ?name .\n"""
        selected_variable_str += ' (GROUP_CONCAT(?name; separator=", ") AS ?authors)'
        group_constraints += 'GROUP BY ?title'
        author_select = True
    if "conference" in selected_variable:
        selected_variable_str += ' ?publishedin'
        if author_select:
            group_constraints += " ?publishedin"
    if len(selected_confs) > 0:
        conf_query = "|".join(selected_confs)
        if not fuzzy_checkbox.state:
            conf_query = "^({})$".format(conf_query)
        select_constraints += f"""FILTER REGEX(?publishedin, "{conf_query}", "i")\n"""
    if "year" in selected_variable:
        selected_variable_str += ' ?year'
        if author_select:
            group_constraints += " ?year"
    if "doi" in selected_variable:
        select_constraints += "?publ dblp:doi ?doi .\n"
        selected_variable_str += " ?doi"
        if author_select:
            group_constraints += " ?doi"
    if year_checkbox.get_state():
        select_constraints += f"""FILTER (?year >= "{year_edit.edit_text.strip()}"^^xsd:gYear)"""
    query = f"""
    PREFIX dblp: <https://dblp.org/rdf/schema#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?title {selected_variable_str} WHERE {{
        ?publ dblp:title ?title .
        ?publ dblp:publishedIn ?publishedin .
        ?publ dblp:yearOfPublication ?year .
        {select_constraints}
    }}
    {group_constraints}
    ORDER BY DESC(?year)
    """
    sparql.setQuery(query)
    # print(query)
    sq = SearchQuery()
    sq.getState()
    with open("asd", "w") as f:
        f.writelines(query)
    with open("query.json", "w") as f:
        f.write(sq.to_json())
    query_text.set_text(query)
    try:
        global ret, isQueried
        ret = sparql.queryAndConvert()
        # print(ret)
        # print(str(h))
        # response_text.set_text(format_output(ret))
        if len(ret["results"]["bindings"]) == 0:
            result_walker.clear()
            result_walker.append(urwid.Text("Find no results!"))
            isQueried = False
            return
        widgets = make_rows(ret)
        result_walker.clear()
        result_walker.extend(widgets)
        isQueried = True
        # for r in ret["results"]["bindings"]:
        #     print(r)
    except Exception as e:
        result_walker.clear()
        result_walker.append(urwid.Text(e))
    

generate_button = urwid.Button("Generate SQL", align="center")
urwid.connect_signal(generate_button, 'click', on_generate_clicked)

def on_load_clicked(botton):
    sq = SearchQuery()
    sq.load_from_file("query.json")

load_button = urwid.Button("Load Previous query", align="center")
urwid.connect_signal(load_button, 'click', on_load_clicked)

ret = None
def on_save_clicked(botton):
    global ret, isQueried
    if ret is not None and isQueried:
        if len(save_fileText.edit_text.strip()) == 0:
            result_walker.clear()
            result_walker.append(urwid.Text("Please input the filename!"))
            return
        header, result = format_output(ret)
        df = pd.DataFrame(result, columns=header)
        df.to_csv(save_fileText.edit_text.strip() + ".csv", index=False)
        result_walker.clear()
        result_walker.append(urwid.Text("Saved!"))
    return

save_button = urwid.Button("Save query result to file: ", align="center")
save_fileText = urwid.Edit("")
save_fileText_bg = urwid.AttrMap(save_fileText, 'file_bg')
urwid.connect_signal(save_button, 'click', on_save_clicked)

buttons_column = urwid.Columns([generate_button, load_button, save_button, save_fileText_bg], 2)
# Build UI list
selection_widgets = [
    name_edit,
    *conf_grid_rows,
    clear_conf_button,
    urwid.Divider(),
    urwid.Text("Select:"),
    *select_grid_rows,
    urwid.Divider(),
    year_checkbox,
    urwid.Divider(),
    buttons_column,
    urwid.Divider('-'),
    # query_text,
    # this is the actual search result should be displayed
]

selection_walker = urwid.SimpleFocusListWalker(selection_widgets)
selection_listbox = urwid.ListBox(selection_walker)

result_walker = urwid.SimpleFocusListWalker([])
result_listbox = urwid.ListBox(result_walker)

# walker = urwid.SimpleFocusListWalker(main_widgets)
# listbox = urwid.ListBox(walker)

# Show/hide year input
def on_checkbox_change(checkbox, new_state):
    if new_state:
        if year_edit_wrap not in selection_walker:
            selection_walker.insert(selection_walker.index(buttons_column), year_edit_wrap)
    else:
        if year_edit_wrap in selection_walker:
            selection_walker.remove(year_edit_wrap)

urwid.connect_signal(year_checkbox, 'change', on_checkbox_change)

# Start UI
combined_body = urwid.Pile([
    ('weight', 2, selection_listbox),  # non-expanding height
    ('weight', 1, result_listbox)          # expands and scrolls
])
palette = [
    ('file_bg', 'default', 'dark blue'),  # (foreground, background)
]
# palette = [('reversed', 'standout', '')]
loop = urwid.MainLoop(combined_body, palette)
loop.run()

# %%
