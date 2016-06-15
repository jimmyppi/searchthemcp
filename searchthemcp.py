#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

"""
The head script to run when updating the search.
Parse the mcp html files and generate all files needed for the update.

Usage:

./searchthemcp.py --download --maxsize=5
"""

import os
import datetime
import re
import json
import argparse

from mcparser import MCPFilesParser, DATADIR
from mcpdb import MCPDB

def getAutoCompletionDict(comics, limit=44):
   """
   Create a map between a string and a list of matching comics:

   {'A': [all comics starting with A],
    'AA': [all comics starting with AA],
    ...
   }
   
   If there are more than @limit comics starting with the key string it is excluded from the map,
   so 'A' will probably never be included if you don't use an extremly large limit.

   Usage
   -----
   with open('file_listing_all_comics.txt', limit=100) as comics:
       d = getAutoCompletionDict(comics)

   Compression
   -----------
   Some tricks are used to make the map smaller:
   * Only include the missing part of the string in the matching list.
     Example: "GUN RUNNER ": ["1","2","3","4","5","6"]
   * If the key contain exactly the same list of matching comics as a longer key, redirect to the longer key.
     Example: "GUN RUNNER": "GUN R"
   * Do not include exact matches.
     Example: "GUN RUNNER 1": [""] is not included in the map
   """

   def lensort(x,y):
     if len(x) > len(y):
       return 1
     else:
       return -1

   d = dict()
   for line in comics:
      line = line.strip()
      for i in range(1,len(line)+1):
         if line[:i] in d:
            d[line[:i]].append(line[i:])
         else:
            d[line[:i]] = [line[i:]]
   dlimit = dict()
   ckeys = d.keys()
   ckeys.sort(cmp=lensort)
   for k in ckeys:
      v = d[k]
      if len(v) > limit:
         # Too many alternatives
         continue
      if len(v) == 1 and v[0] == "":
         # Do not include exact matches, example: "GUN RUNNER 1":[""] is excluded from the dict
         continue
      else:
         for i in range(1,len(k)):
            if k[:i] in dlimit and len(dlimit[k[:i]]) == len(v):
               # If the matches list is the same, redirect, example: "GUN RUNNER":"GUN R"
               dlimit[k] = k[:i]
               break
      if not k in dlimit:
         dlimit[k] = v
   
   return dlimit

def createFiles(update_source_files=False, sql_files_max_size=5):
   """
   Create all files needed for a searchthemcp update in the directory 'data/YYYY-MM-DD':
   
   * comicsAutoComplete.js    - Data used by the auto completion functionality
   * comics_sql.txt           - SQL statements for building the comics database
   * figures_sql.txt          - SQL statements for the characters database
   * comics_fullname_sql.txt  - SQL statements for the comics full name database
   
   Also create:
   * comics.txt    - List of all found comics.
   * anomalies.txt - List of anomalies.

   Parameters
   ----------

   * update_source_files: If True, download all mcp html files to data/mcp/.
   * sql_files_max_size:  Max size in MB of the SQL statements files.
   """
   parser = MCPFilesParser()
   
   def comicSorter(x,y):
      def fixNr(c):
         abbr,nr = parser._getAbbreviationAndNumber(c)
         if nr:
            m = re.search(r'^(\d*)', nr)
            if m:
               base_nr = m.group(1)
               return '%s %s%s' % (abbr, '0'*(4-len(base_nr)), nr)
         return c
      x = fixNr(x)
      y = fixNr(y)
      
      if x > y:
         return 1
      elif y > x:
         return -1
      else:
         return 0
   
   if update_source_files:
      parser.updateMCPFiles()
   figures,comics,anomalies = parser.getFiguresAndComics(verbose=True)
   
   outputdir = os.path.join(DATADIR, datetime.datetime.now().strftime('%Y-%m-%d'))
   if not os.path.isdir(outputdir):
      os.mkdir(outputdir)
   
   with open(os.path.join(outputdir, "anomalies.txt"), 'w') as anom_out:
      anom_out.write(str(anomalies))
   
   comics_str = comics.keys()
   comics_str.sort(cmp=comicSorter)
   with open(os.path.join(outputdir, "comics.txt"), 'w') as comics_out:
      for c in comics_str:
         comics_out.write('%s\n' % c)
   
   with open(os.path.join(outputdir, "comics.txt")) as comics_in:
      acd = getAutoCompletionDict(comics_in)
   acd = json.dumps(acd)
   with open(os.path.join(outputdir, "comicsAutoComplete.js"), 'w') as auto_comp_out:
      auto_comp_out.write("var comics = %s;" % acd)
   
   db = MCPDB('mcp_figures', 'mcp_comics', 'mcp_comics_fullname')
   
   max_size = sql_files_max_size*1024*1024
   
   def writeSql(gen, file_name):
      s = 0
      n = 0
      
      sql_out = open(os.path.join(outputdir, "%s#%d.txt" % (file_name, n)), 'w')
      for sql in gen:
         sql_ = '%s;\n' % sql
         if s + len(sql_) > max_size:
            s = 0
            n += 1
            sql_out.close()
            sql_out = open(os.path.join(outputdir, "%s#%d.txt" % (file_name, n)), 'w')
         s += len(sql_)
         sql_out.write(sql_)
      sql_out.close()
   
   writeSql(db.generateSqlForComics(comics), 'comics_sql')
   writeSql(db.generateSqlForComicsFullName(comics), 'comics_fullname_sql')
   writeSql(db.generateSqlForFigures(figures), 'figures_sql')
   
if __name__ == '__main__':
   parser = argparse.ArgumentParser(description='Generate all files needed for an update of the mcp search.')
   parser.add_argument('--download', action='store_true', help="If provided, download mcp files.")
   parser.add_argument('--maxsqlsize', type=int, default=5, help="Max size (Mb) of the sql statement files.")
   args = parser.parse_args()
   createFiles(update_source_files=args.download, sql_files_max_size=args.maxsqlsize)
