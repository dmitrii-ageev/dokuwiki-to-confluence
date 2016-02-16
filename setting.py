doku_data_path = "/home/ivan/vo/doku/data"
space = "IT"
parent_page = "12649988"  # set page id, can find id by https://confluence.atlassian.com/display/CONFKB/How+to+Get+Confluence+Page+ID+From+The+User+Interface

# line fixup
fixup_line = {
    r'Copy {{scripts\\*}} to the new machine':
    r'Copy {{scripts\ \*}} to the new machine'
}

# dictionary mapping DokuWiki user to Confluence user
doku_confluence_user = {
    b'joes' : 'joe.smith',
    b'ivan' : 'ivan.kanis'
}
