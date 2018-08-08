dokuwiki-to-confluence
======================

Two scripts to import data from DokuWiki to Confluence

Usage:
------
To use this conversion:

- edit settings.py file
	* provide path to doku data path
	* provide Confluence space you wish to export to
	* provide Confluence parent page id
	* provide a dictionary mapping DokuWiki user to Confluence user
	* you may need to add fixup line if Confluence reject a page

- Modify 'import-confluence.py' to configure:
	* user name
	* password
	* confluence URL

- run import-confluence.py

If you want to fix Confluence page's author name you will have to install phpserialize and do the following:

- run create-sql-script.py

- run the sql script on the Confluence server

Examples:
---------

    $ python3 import-confluence.py

(You can add -p flag if you want the script to prompt for a password instead of using the one on the file)

    $ pip3 install phpserialize
    $ python3 create-sql-script.py

Copy the generated script fix-author.sql to the the confluence server and execute it.

    # su - postgres
    $ psql -d confluencedb < /tmp/fix-author.sql

Authors
-------

Ivan Kanis <github@kanis.fr> and some improvements were made by Dmitrii Ageev <d.ageev@gmail.com>

