# -*- coding: iso-8859-1 -*-
"""
Provide the class MCPDB for generating sql statements for inserting figures and comics data into the MySQL database.
"""

import MySQLdb
sqlEscape = MySQLdb.escape_string

class MCPDB:
   """
   There are three mysql tables that need to be created.

   Generate the sql statements with:
   * generateSqlForFigures
   * generateSqlForComics
   * generateSqlForComicsFullName
   """
   
   def __init__(self, figtable, comictable, fullnametable):
      self._figtable = figtable
      self._comictable = comictable
      self._fullnametable = fullnametable
      
   def generateSqlForFigures(self, figures):
      yield self._sqlCreateFigureTable(self._figtable)
      yield self._sqlDeleteAllFromTable(self._figtable)
      for f in figures:
         yield self._sqlInsertFigure(self._figtable, f)
         
   def generateSqlForComics(self, comics):
      yield self._sqlCreateComicTable(self._comictable)
      yield self._sqlDeleteAllFromTable(self._comictable)
      for comic in comics.values():
         for sql in self._sqlInsertComic(self._comictable, comic):
            yield sql
            
   def generateSqlForComicsFullName(self, comics):
      yield self._sqlCreateComicFullnameTable(self._fullnametable)
      yield self._sqlDeleteAllFromTable(self._fullnametable)
      for comic in comics.values():
         yield self._sqlInsertComicFullname(self._fullnametable, comic)
   
   def _sqlDropTable(self, table_name):
      return 'DROP TABLE %s' % table_name
      
   def _sqlDeleteAllFromTable(self , table_name):
      return 'DELETE FROM %s' % table_name
   
   def _sqlCreateFigureTable(self, table_name):
      """
      Columns:
      * figid       - Internal figure id
      * name        - The name of the figure
      * race        - For example "Skrull", "Kree", etc
      * search_name - All variants of the figure name
      * link        - Url to the figure list
      * dimension   - For example "Ultimate universe", "2099", etc
      * chronolist  - The figure chronlogical list extracted from the mcp html files.
      """
      return ("CREATE TABLE IF NOT EXISTS %s (figid int, name varchar(256), race varchar(128), search_name text, "
              "link varchar(128), dimension varchar(128), chronolist longtext, index (figid), index (name, search_name(512)), index (race))") % table_name
   
   def _sqlCreateComicTable(self, table_name):
      """
      Columns:
      * comicid         - Unique internal id for a comic
      * abbreviation    - For example 'IM 73'
      * appendix        - For example '-FB', or '' if no appendix
      * figid           - figure id
      * entry_index     - Entry index in figure chronolist
      * current_raw     - Entry in chronolist
      * current_comics  - comic1_abbr|comic1_id|comic1_appendix#comic2_abbr|...
      * next_raw        - Next entry in chronolist
      * next_comics     - comic1_abbr|comic1_id|comic1_appendix#comic2_abbr|...
      * previous_raw    - Previous entry in chronolist
      * previous_comics - comic1_abbr|comic1_id|comic1_appendix#comic2_abbr|...
      """
      return ("CREATE TABLE IF NOT EXISTS %s (comicid int, abbreviation varchar(128), appendix varchar(128), figid int, "
              "entry_index int, current_raw varchar(128), current_comics text, next_raw varchar(128), next_comics text, "
              "previous_raw varchar(128), previous_comics text, index (comicid), index (abbreviation), index (figid, entry_index))") % table_name

   def _sqlCreateComicFullnameTable(self, table_name):
      """
      Columns:
      * comicid   - Unique int id for a comic
      * full_name - Full name for a comic, for example "IRON MAN 73"
      """
      return "CREATE TABLE IF NOT EXISTS %s (comicid int, full_name text, index (comicid))" % table_name

   def _sqlInsertFigure(self, t, f):
      return "INSERT INTO %s VALUES ('%d','%s','%s','%s','%s','%s','%s')" % (t, 
                                                                             f['id'], 
                                                                             sqlEscape(f['name']), 
                                                                             sqlEscape(f['race']), 
                                                                             sqlEscape(f['search']), 
                                                                             sqlEscape(f['link']), 
                                                                             sqlEscape(f['dimension']), 
                                                                             sqlEscape(f['chronolist'])
                                                                             )
   
   def _sqlInsertComicFullname(self, t, comic):
      return "INSERT INTO %s VALUES ('%d','%s')" % (t, comic['id'], sqlEscape(comic['full_name']))

   def _sqlInsertComic(self, t, comic):
      for app,figs in comic['appendixes'].items():
         for figid,figdatalist in figs.items():
            for figdata in figdatalist:
               current_raw = figdata['current']['rawstr']
               next_raw = figdata['next']['rawstr']
               prev_raw = figdata['previous']['rawstr']
               yield "INSERT INTO %s VALUES ('%d','%s','%s','%d','%d','%s','%s','%s','%s','%s','%s')" % (t, 
                                                                                                         comic['id'], 
                                                                                                         sqlEscape(comic['abbreviation']), 
                                                                                                         sqlEscape(app), 
                                                                                                         figid, 
                                                                                                         figdata['index'], 
                                                                                                         sqlEscape(current_raw), 
                                                                                                         sqlEscape('#'.join(['|'.join([c['comicstr'], str(c['comicid']), c['appendix']]) for c in figdata['current']['comics']])), 
                                                                                                         sqlEscape(next_raw), sqlEscape('#'.join(['|'.join([c['comicstr'], str(c['comicid']), c['appendix']]) for c in figdata['next']['comics']])),
                                                                                                         sqlEscape(prev_raw), sqlEscape('#'.join(['|'.join([c['comicstr'], str(c['comicid']), c['appendix']]) for c in figdata['previous']['comics']])) 
                                                                                                         )
