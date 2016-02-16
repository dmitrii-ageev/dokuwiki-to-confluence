# produce .sql script that will be executed on the server
# the purpose is to change the author name of the wiki page

import os
from os.path import join
import sys
import phpserialize

# settings
from setting import doku_data_path, doku_confluence_user, space

sql_script = open ('fix-author.sql', 'w')

def save(pagename, last_change_user):
    sql_statement = """
update content set creator = (select user_key from user_mapping where lower_username = '{0}')
 where contentid in (select c2.contentid from content c2 where c2.title = '{1}'
                     and spaceid = (select spaceid from spaces where spacekey = '{2}'));
""".format(last_change_user, pagename, space)
    sql_script.write(sql_statement)

top_page = join(doku_data_path, 'pages')
for project_dir, subdirs, files in os.walk(top_page):
    for filename in files:
        if filename[-4:] == '.txt':
            pagename = filename.replace('_',' ').strip()
            pagename = pagename[:-4]

            meta_file = (join (project_dir.replace('pages', 'meta'), filename[:-4] + '.meta'))
            with open (meta_file, 'rb') as f:
                data = phpserialize.load(f)
            last_change_user = data[b'persistent'][b'last_change'][b'user']
            last_change_user = doku_confluence_user[last_change_user]

            save (pagename, last_change_user)

sql_script.close()

# Local Variables:
# compile-command: "python3 create-sql-script.py"
# End:

# vim:et:sw=4:ts=4:

