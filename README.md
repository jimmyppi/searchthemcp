Add search functionality to the Marvel Chronology Project.

Getting started
---------------

* You need a computer with python2.* to run the script that parses the files from chronologyproject.com and generates the database files.
* You also need a server with php and mysql.

Set up the search
-----------------

1. Upload the files in the web directory (web/) to the server.
2. Change mysql login credentials in mcpfunctions.php on the server:

   ´´´PHP
   function openConnection() {
      $host = "localhost";
      $login= "YOUR_MYSQL_USERNAME";
      $dbname = "THE_DATABASE_NAME";
      $password= "YOUR_MYSQL_PASSWORD";
   ´´´

3. Run the script:
   ´´´Shell
   $ ./searchthemcp.py --download
   ´´´
   This will download all files from chronologyproject.com and store them in data/mcp.
   The files are parsed and database files are stored in data/todays-date/
4. Watch out for parser warnings in the output from the script. Fix bad html syntax and run the script again, now without the --download flag.
5. Solve everything in the anomalies file: data/todays-date/anomalies.txt. Run the script again until you get an empty anomalies file.
6. Upload data/todays-date/comicsAutoComplete.js to the server directory autocomplete/
7. Upload database files in data/todays-date, for example by using phpMyAdmin on the server to import the files. The files must be imported in the numbered ordering of the files.
   
   Three database tables will be created:
   * mcp_comics: Created by comics_sql#*.txt
   * mcp_comics_fullname: Created by comics_fullname_sql#*.txt
   * mcp_figures: Created by figures_sql#*.txt

   The files are by default split so that they never become larger than 5 Mb. You can get timeouts from phpMyAdmin if you try to transfer too large files. The split size can be provided when running the script. For example, to increase the file size to 10 Mb:
   ´´´Shell
   $ ./searchthemcp.py --maxsqlsize 10
   ´´´
8. Test so that everything seem to be working and update the last update date in web/searchthemcp.php.

Help output from the script
---------------------------

´´´Shell
$ ./searchthemcp.py -h
usage: searchthemcp.py [-h] [--download] [--maxsqlsize MAXSQLSIZE]

Generate all files needed for an update of the mcp search.

optional arguments:
  -h, --help            show this help message and exit
  --download            If provided, download mcp files.
  --maxsqlsize MAXSQLSIZE
                        Max size (Mb) of the sql statement files.
´´´

Contents of searchthemcp
------------------------

* mcparser.py - Module for parsing of the files from chronologyproject.com.
* mcpdb.py - Module for generation of database query files.
* searchthemcp.py - Script for parsing and generation of database files.
* web/ - php and javascript files for the frontend
* data/ - Location of files generated by the script
