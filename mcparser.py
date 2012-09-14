# -*- coding: iso-8859-1 -*-
"""
Provide the class MCPFilesParser for extracting data from the mcp files needed by the search.

Usage
-----
parser = MCPFilesParser()
# Download and store all mcp files:
parser.updateMCPFiles()
# Parse:
comics, figures, anomalies = parser.getFiguresAndComics()
"""

import re
import os
import urllib2
from cStringIO import StringIO

DATADIR = os.path.join(os.path.dirname(__file__), 'data')
MCPFILESDIR = os.path.join(DATADIR, 'mcp')

class Anomalies(dict):
   """Extension of dict for storing and printing of anomalies in the mcp files"""

   def add(self, abbr, fig_name, comicstr, reason):
      """
      Add an anomaly to the dict

      * abbr     - The comic abbreviation, for example AMS, DD2 etc.
      * fig_name - The figure name where the anomaly was found.
      * comicstr - The actual row from the figure's chronology list that contain the anomaly.
      * reason   - Description of the anomaly.
      """
      if not abbr in self:
         self[abbr] = dict()
      if not comicstr in self[abbr]:
         self[abbr][comicstr] = {'reason':reason, 'figures': []}
      if not fig_name in self[abbr][comicstr]['figures']:
         self[abbr][comicstr]['figures'].append(fig_name)
         
   def __str__(self):
      """Return a pretty string of the anomalies"""
      abbrs = self.keys()
      abbrs.sort()
      b = StringIO()
      def write(s=''):
         b.write('%s\n' % s)
      for abbr in abbrs:
         anom = self[abbr]
         write(abbr)
         write('==============')
         for comic,d in anom.items():
            write(comic)
            write(d['reason'])
            write('\n'.join(d['figures']))
            write('--------------')
         write('==============')
         write('\n')
      return b.getvalue()
      
class ParseError(Exception):
   """Raised by MCPFilesParser if something goes terribly wrong with the parsing"""
   pass

class MCPFilesParser:
   """
   Parser class for the mcp files
   
   Usage
   -----
   >> parser = MCPFilesParser()

   Download all mcp files:
   >> parser.updateMCPFiles()

   Extract figure chronology lists and comics in the mcp files: 
   >> comics, figures, anomalies = parser.getFiguresAndComics()

   See getFiguresAndComics documentation for data structure of comics, figures and anomalies

   Sanity check
   ------------
   All extracted comic abbreviations must exist in the mcp key.
   If not, it is assumed that the parser did not understand the comic string syntax and an anomaly is created.
   """

   BASEURL = 'http://www.chronologyproject.com/'
   
   MCPFILES = [chr(c) for c in range(ord('a'), ord('z')+1)]
   SINGLEFIGURES = [("CAPTAIN AMERICA Chronology Page", "capa"),
                    ("HULK Chronology Page", "hulk"),
                    ("IRON MAN Chronology Page", "ironman"),
                    ("MR. FANTASTIC Chronology Page", "mrfantastic"),
                    ("SCARLET WITCH Chronology Page", "witch"),
                    ("SPIDER-MAN Chronology Page", "spidey"),
                    ("STORM Chronology Page", "storm"),
                    ("SUB-MARINER Chronology Page", "namor")
                    ]
   
   MCPDIMENSIONS = [('killraven', 'Killraven Mythos'),
                    ('newu', 'New Universe'),
                    ('2099', '2099'),
                    ('ultimate', 'Ultimate Universe'),
                    ('aoa', 'Age of Apocalypse'),
                    ('heroesreborn', 'Heroes Reborn'),
                    ]
                   
   KEYFILE = 'key'
   FILEEND = '.php'

   # Regular expressions for parsing
                         
   re_find_figures = re.compile(r'\n(\n|<b>)(?P<figure>.*?)(\n<p>|\n</span></p>|\n<hr>|\n<br>)', re.DOTALL | re.IGNORECASE)
   re_link_name = re.compile(r'<a[^>]*?name="(?P<link_name>.*?)"')
   
   re_body = re.compile(r'key.gif(?P<body>.*?)key.gif', re.DOTALL)
   re_body_single_fig = re.compile(r'</table>(?P<body>.*?)key.gif', re.DOTALL)
   re_body_killraven = re.compile(r'</h1>(?P<body>.*?)<font', re.DOTALL)
   
   re_tag = re.compile(r'<[^>]*?>')
   
   re_to_remove = re.compile(r'[\[\{\}\]]')
   re_cf = re.compile(r'\|\s*cf[^\|]+(\||$)')
   
   figure_redirections = ["(~", "(See", "See", "(From","From", "Note", "Caution", "(may continue","may continue","between"]
   comic_appendixes = ["-FB", "-BTS", "-OP","-VO", "(", "pg", "Pg"]
   
   re_appendix = r'(\([\d\-\: ]+\)|pg[pgn\- d]+|)(\-(FB|BTS|OP|VO))*'
   
   abbr_rex = r'( ?[A-Z]+[/\-&\:\.]?)+[@\d\.\?]?(?= |$)'
   nr_rex = r"['-]?\d*[/\.]?\d+(?=$)"
   
   re_abbr_nr = re.compile(r"^(?P<abbr>.+?) (?P<nr>['-]?[\.\d]*[A-B]?/?\d+[A-B]?(?=$))")

   def getFiguresAndComics(self, verbose=False):
      """
      Extract figures and comics from the mcp files
      
      Return:
      * figures   - List of all figures. See _getFigures for data structure documentation.
      * comics    - Dict with all comics. See _cleanAndCollectComics for data structure documentation.
      * anomalies - All syntax anomlies found, instance of the class Anomalies.
      """
      self.abbrs = self._getAbbreviations()
      figures = self._getFigures(verbose)
      comics = dict()
      anomalies = Anomalies()
      
      for i,f in enumerate(figures):
         if not 'name' in f:
            fig_name = self._clean(f['chronolist'][:f['chronolist'].lower().find('<br>')], False)
            f['chronolist'] = f['chronolist'][f['chronolist'].lower().find('<br>') + 4:]
            #if verbose:
            #   print 'CAC: ' + fig_name + '|'
            f['name'] = fig_name
         m = re.search(r'\[(?P<race>[^\]]+)\]', f['name'])
         if not m:
            f['race'] = ''
         else:
            f['race'] = m.group('race')
         fig_search = self._cleanAndCollectComics(i, f['chronolist'], comics, anomalies, f['name'], verbose)
         f['id'] = i
         f['search'] = fig_search
      return figures, comics, anomalies
      
   def updateMCPFiles(self, verbose=True):
      """Download all mcp files and store in MCPFILESDIR"""
      if(not os.path.isdir(MCPFILESDIR)):
         os.mkdir(MCPFILESDIR)
      files_to_download = self.MCPFILES[:]
      files_to_download.append(self.KEYFILE)
      files_to_download.extend([u for _,u in self.SINGLEFIGURES])
      files_to_download.extend([u for u,_ in self.MCPDIMENSIONS])
      for f in files_to_download:
         f += self.FILEEND
         if verbose:
            print 'Downloading %s' % f
         urlin = urllib2.urlopen(self.BASEURL + f)
         data = urlin.read()
         urlin.close()
         with open(os.path.join(MCPFILESDIR, f), 'w') as fileout:
            fileout.write(data)
         
   def _readFile(self, f):
      """Read mcp file with name @f from disk and return the contents"""
      with open(os.path.join(MCPFILESDIR, f + self.FILEEND), 'r') as inp:
         return inp.read()
      
   def _getAbbreviations(self):
      """
      Parse mcp key and return all abbreviations mapped to the full name of the title:
      {'A': 'Avengers',
       'A2': 'Avengers v2',
       ...
       }
      """
      key = self._readFile(self.KEYFILE)
      m = re.search(r'TITLE KEY By KEY(?P<body>.*?)(?=TITLE KEY By TITLE)', key, re.DOTALL + re.I)
      body = m.group('body')
      re_key = r'<tr><td>(?P<abbr>[^>]*)</td?><td>(?P<title>[^>]*)<'
      abbr_dict = {
                     'MARVEL MYSTERY COMICS': 'MARVEL MYSTERY COMICS',
                     'US1': 'US1',
                     'UX/FF': 'UX/FF',
                     'MYSTIC COMICS': 'MYSTIC COMICS',
                     'RED RAVEN': 'RED RAVEN',
                     'SUN GIRL': 'SUN GIRL',
                     'W3': 'WOLVERINE VOL. 3',
                     'WORLD OF FANTASY': 'WORLD OF FANTASY',
                     'RINGO KID WESTERN': 'RINGO KID WESTERN',
                     'BATTLETIDE': 'BATTLETIDE',
                     'PPSM': 'PPSM',
                     'GOTG': 'GOTG',
                     'NAMORA COMICS': 'NAMORA COMICS',
                     'N:EA': 'N:EA',
                     'MEKANIX': 'MEKANIX',
                     'KID KOMICS': 'KID KOMICS',
                     'REDEYE': 'REDEYE',
                     'WESTERN GUNFIGHTERS': 'WESTERN GUNFIGHTERS',
                     'G-S KID COLT': 'G-S KID COLT',
                     'MYSTERY TALES': 'MYSTERY TALES',
                     'CIVIL WAR': 'CIVIL WAR',
                     'NFHC': "NICK FURY'S HOWLING COMMANDOS",
                     'NEW TEEN TITANS': 'NEW TEEN TITANS',
                     'GENE': 'GENETIX'
                  }
      for m in re.finditer(re_key, body):
         abbr = self._clean(m.group('abbr'), False)
         title = self._clean(m.group('title'), False)
         if not abbr in ['@', "'"]:
            abbr_dict[abbr] = title
      return abbr_dict
      
   def _getSingleFigureFileList(self, name_line, verbose=False):
      """
      Check if the string @name_line matches any figures that have their chronlogy list on their own page.
      
      Return the chronolist and the url to the page if a match is found, else return None, None
      """
      for n, f in self.SINGLEFIGURES:
         if name_line.find(n) != -1:
            if verbose:
               print 'Parsing single figure list %r' % f
            thelink = self.BASEURL + f
            content = self._readFile(f)
            m_body = self.re_body_single_fig.search(content)
            if not m_body:
               raise ParseError('No chronological list found in %s' % f)
            body = m_body.group('body')
            fig_list = self.re_find_figures.search(body).group('figure')
            return fig_list, thelink
            
      return None,None
         
   def _getFiguresListsOldSyntax(self, files, verbose=False):
      """
      For the old syntax, without expand/collapse
      
      Collect all figures in the mcp files
      Return list of figures where each figure is a dict with:
      * chronolist - The raw string for the figure (inlcuding html tags etc)
      * dimension  - The dimension of the figure (for example 'Ultimate')
      * link       - Url to the figure
      """
      
      figures = []
      
      #files = [{'c.htm':'wsdtg'}]
      for f,dim in files:
         
         if verbose:
            print 'Parsing file %r' % f
         content = self._readFile(f)
         nfigs = len(figures)
         
         # Get figure lists
         m_body = self.re_body.search(content)
         if m_body:
            body = m_body.group('body')
         else:
            m_body = self.re_body_killraven.search(content)
            if m_body:
               body = m_body.group('body')
            else:
               raise ParseError('No figures found in %s' % f)

         body = body.replace('<p><b>','<p>\n\n<b>')# Fix for Spider-Man II
         
         # Separate figures
         for m in self.re_find_figures.finditer(body):
            fig_list = m.group('figure')
            thelink = ''
            if fig_list.lower().find('<br>') == -1:# False hit (\n\n\n<hr> for example)
               continue
            
            first_row = fig_list[:fig_list.lower().find('<br>')]
            
            # Search single figure files
            single_fig_list,single_link = self._getSingleFigureFileList(first_row, verbose)
            if single_fig_list:
               fig_list = single_fig_list
               thelink = single_link
            
            # Fix some details
            if first_row.lower().find('<b>') == -1:
               fig_list = '<b>'+fig_list
            if first_row.lower().find('</b>') == -1:
               fig_list = fig_list[:fig_list.lower().find('<br>')]+'</b>'+fig_list[fig_list.lower().find('<br>'):]
            fig_list = fig_list.replace('<a href="#','<a href="%s%s#' % (self.BASEURL, f))
            
            if not thelink:
               thelink = self.BASEURL + f
               m = self.re_link_name.search(first_row)
               if m:
                  thelink += '#%s' % m.group('link_name')
                  if verbose:
                     print 'Link name:', m.group('link_name'), [first_row]
            
            figures.append({'chronolist': fig_list, 'dimension': dim, 'link': thelink})

         if verbose:
            print 'Found %d figures in %r' % (len(figures) - nfigs, f)
      
      return figures
      
   def _getFiguresListsNewSyntax(self, files, verbose=False):
      """
      For the expand/collapse syntax
      
      Collect all figures in the mcp files
      Return list of figures where each figure is a dict with:
      * chronolist - The raw string for the figure (inlcuding html tags etc)
      * dimension  - The dimension of the figure (for example 'Ultimate')
      * link       - Url to the figure
      """
   
      re_fig = re.compile(r'<(p id=|a name=)"(?P<id>[^"]+)"><span class="char">(?P<name>.+)</span><br>', re.I)
      re_fig_nolist = re.compile(r'(<p( id="(?P<id>[^"]+)"|)>(<span class="char">|)<b>|</span></p>|<p></p>|<span></p><b>)(?P<name>.+)(<br>|</p>|</a></b>)', re.I)
      
      figures = []
      
      for f,dim in files:
      
         # Read file
         if verbose:
            print 'Parsing file %r' % f
         content = self._readFile(f)
         content = content.split('\n')
         
         i = 0
         nfigs = len(figures)
         first_found = False
         while i < len(content):
            line = content[i]
            if first_found and line.lower().find('<hr>') == 0:
               # End of file
               break
               
            m = re_fig.search(line) or re_fig_nolist.search(line)
            if m:
               # Found a figure!
               figname = self._clean(m.group('name'),False)
               name_i = i
               figid = m.group('id')
               thelink = self.BASEURL + f
               if figid:
                  thelink += '#%s' % figid
               #if verbose:
               #   print '%s|' % figname
               first_found = True
               i += 1
               if content[i].lower().find('<span class="chron">') == 0:
                  #print '%d NOT OK FIGLIST: %s' % (i-1,line)
                  i += 1
               while not content[i].startswith('</span></p>') != 0 and not content[i].startswith('</p>') and not content[i].startswith('<p></p>') and not content[i].startswith('</font></span></p><font>'):
                  # While not end of figure list
                  i += 1
               i += 1
               
               if content[i].strip() and content[i].lower().find('<hr>') != 0:
                  if verbose:
                     print 'Warning! Line %d should be empty: %s, %s' % (i, [content[i]], line)
               if content[i].find('<hr>') == 0:
                  # End of file
                  break
                  
               # Search single figure files
               single_fig_list,single_link = self._getSingleFigureFileList(content[name_i], verbose)
               if single_fig_list:
                  figures.append({'chronolist':single_fig_list, 'dimension': dim, 'link': single_link})
                  i += 1
                  continue
                     
               fig_list = '\n'.join(content[name_i+1:i])
               
               figures.append({'name': figname, 'chronolist': fig_list, 'dimension': dim, 'link': thelink})
               i += 1
               
            elif first_found:
               if verbose:
                  print 'Warning! Line %d is not an ok figure: %s' % (i, line)
               i += 1
            else:
               i += 1
               
            while not content[i].strip():
               i += 1

         if verbose:
            print 'Found %d figures in %r' % (len(figures) - nfigs, f)
         
      return figures
      
   def _getFigures(self, verbose=False):
      """
      Extract all figures and their chronlogical lists from the mcp files.

      Return list of figure dicts with the contents:
      * chronolist - The raw html that contain figure name and chronological list.
      * dimension  - Name of the dimension the figure come from (standard, 2099, ultimate etc)
      * link       - The link to the figure, examples:
                     http://chronologyproject.com/a.php#ANGEL_III
                     http://chronologyproject.com/spidey.php
                     ...
      """
      # Files with the expand/collapse functinality
      new_syntax_files = [(f, 'standard') for f in self.MCPFILES]
      # Files without expand/collapse
      old_syntax_files = self.MCPDIMENSIONS[:]
   
      figures = self._getFiguresListsNewSyntax(new_syntax_files, verbose)
      figures.extend(self._getFiguresListsOldSyntax(old_syntax_files, verbose))
      return figures
         
   def _anomalyDetector(self, comicstr, abbr, nr, fig_name, anomalies):
      """
      Check that the parser understand the syntax of the comic string and
      that the extracted abbreviation exist in the mcp key.
      """
      abbr_chars = 'A-Z@ \-\:&/\?\.'
      nr_chars = "\d/'\-\."
      if re.search(r"[^%s%s]" % (abbr_chars,nr_chars), comicstr):
         anomalies.add(abbr, fig_name, comicstr, 'Unexpected character')
         return
      if not abbr in self.abbrs:
         anomalies.add(abbr, fig_name, comicstr, 'Unknown abbreviation')
         
   def _getFullComicName(self, abbr, nr, isAnnual):
      """
      Translate the abbreviated comic name to the full comic name:
      A2 1 >> AVENGERS VOL. 2 1
      """
      fname = self.abbrs.get(abbr, abbr)
      if isAnnual:
         fname += ' ANNUAL'
      if nr:
         return '%s %s' % (fname, nr)
      else:
         return fname
            
   def _cleanAndCollectComics(self, fig_index, fig_list, comic_dict, anomalies, fig_name, verbose=False):
      """
      Collect comics from a figure's chronology list

      Store data in comic_dict which contains a rather complicated data structure for each unique comic.
      All figures appearing in a comic are stored in this structure together with which comic the figures appear in before and after.

      Comic dict example for "W2 1"
      -----------------------------

      {'w2 1': {'abbreviation': 'W2 1',
                'appendixes': {'': {6536:  [{'current':  {'comics': [{'appendix': '', 'comicid': 18012, 'comicstr': 'W2 1'}],
                                                          'rawstr': 'W2 1'},
                                             'index':    26,
                                             'next':     {'comics': [{'appendix': '', 'comicid': 18013, 'comicstr': 'W2 2'}],
                                                          'rawstr': 'W2 2'},
                                             'previous': {'comics': [{'appendix': '', 'comicid': 3978, 'comicstr': 'UX 206'}],
                                                          'rawstr': 'UX 206'}}],
                                    11516: [{'current':  {'comics': [{'appendix': '', 'comicid': 18012, 'comicstr': 'W2 1'}],
                                                          'rawstr': 'W2 1'},
                                             'index':    620,
                                             'next':     {'comics': [{'appendix': '', 'comicid': 18013, 'comicstr': 'W2 2'}],
                                                          'rawstr': 'W2 2'},
                                             'previous': {'comics': [{'appendix': '', 'comicid': 18420, 'comicstr': 'M/CP 10'}],
                                                          'rawstr': 'M/CP 10'}}]},
                           '-BTS': {9734:  [{'current':  {'comics': [{'appendix': '-BTS', 'comicid': 18012, 'comicstr': 'W2 1'}],
                                                          'rawstr': 'W2 1-BTS'},
                                             'index':    145,
                                             'next':     {'comics': [{'appendix': '', 'comicid': 18013, 'comicstr': 'W2 2'}],
                                                          'rawstr': 'W2 2'},
                                             'previous': {'comics': [{'appendix': '', 'comicid': 3978, 'comicstr': 'UX 206'}],
                                                          'rawstr': 'UX 206'}}],
                                    11624: [{'current':  {'comics': [{'appendix': '-BTS', 'comicid': 18012, 'comicstr': 'W2 1'}],
                                                          'rawstr': 'W2 1-BTS'},
                                             'index':    19,
                                             'next':     {'comics': [{'appendix': '-FB', 'comicid': 12260, 'comicstr': 'W:DOOMBRINGER'}],
                                                          'rawstr': 'W:DOOMBRINGER-FB'},
                                             'previous': {'comics': [{'appendix': '', 'comicid': 18435, 'comicstr': 'KP&W 6'}],
                                                          'rawstr': 'KP&W 6'}}]}},
                'full_name': 'WOLVERINE VOL. 2 1',
                'id': 18012}
      }
      

      Parameters
      ----------

      * fig_index  - Figure id.
      * fíg_list   - The figure's raw chronology list as a string.
      * comic_dict - Dictionary with all comics:
                     { Comic string: { id:           Comic id,
                                       abbreviation: Abbreviated comic string,
                                       full_name:    full_comicstr,
                                       appendixes: { appendix { figid: { index:    Entry index
                                                                         next:     { rawstr: "The raw list entry in the figure chronology list",
                                                                                     comics: [{comicstr: str, comicid: id, appendix: app}, ...]
                                                                                    },
                                                                         previous: { rawstr: "The raw list entry in the figure chronology list",
                                                                                     comics: [{comicstr:str, comicid:id, appendix:app}, ...]
                                                                                    },
                                                                        current:  { rawstr: "The raw list entry in the figure chronology list",
                                                                                    comics: [{comicstr:str, comicid:id, appendix:app}, ...]
                                                                                   },
                                                                       },
                                                                ...
                                                              },
                                                     ...
                                                   },
                                       ...
                                     },
                       ...
                     }
      * anomalies  - Dictionary with possible syntax bugs:
                     { comic_abbr: { comicstr: { figures: [figname, ...],
                                                 reason:  "reason"
                                               },
                                     ...
                                   },
                       ...
                     }
      * fig_name   - The name of the figure.
      

      Return
      ------

      * fig_search - String with all variants of a figure name comma separated, example: "SCHEMER/RICHARD FISK, Rose".

      """
      
      def addComic(comicstr, full_name):
         if not comicstr in comic_dict:
            comic_dict[comicstr] = {'id': len(comic_dict), 'abbreviation': comicstr, 'full_name': full_name, 'appendixes': dict()}
      
      def addAppendix(comicstr, appendix, figid, previous, rawstr, entry_index, current):
         if not appendix in comic_dict[comicstr]['appendixes']:
            comic_dict[comicstr]['appendixes'][appendix] = dict()
         if not figid in comic_dict[comicstr]['appendixes'][appendix]:
            comic_dict[comicstr]['appendixes'][appendix][figid] = []
         comic_dict[comicstr]['appendixes'][appendix][figid].append({'index': entry_index, 'next': dict(rawstr='', comics=[]), 'previous': previous, 'current': current})
         
      def setNext(comicstr, appendix, figid, next_comic, current_entry_index):
         if comic_dict[comicstr]['appendixes'][appendix][figid][-1]['index'] == current_entry_index:
            comic_dict[comicstr]['appendixes'][appendix][figid][-2]['next'] = next_comic
         else:
            comic_dict[comicstr]['appendixes'][appendix][figid][-1]['next'] = next_comic

      re_br = re.compile('<br>', re.I)
      fig_list = re_br.split(fig_list)
      
      fig_search = fig_name[:] # The name including 'See' and 'From' redirections 
      extra_search = [] # See and From redirections
         
      previous = dict(rawstr='', comics=[])
      for i in range(len(fig_list) - 1):
         rawstr = fig_list[i].strip()
         comics,rawstr,e = self._clean(rawstr)
         
         current = dict(rawstr=rawstr, comics=[])
         if e:
            extra_search.append(e)
         
         for c in comics:
            if c:
               thecomic, theappendix = self._getComicAndAppendix(c)
               if thecomic == 'CA152':
                  thecomic = 'CA 152' # Special fix for Scorpion II
               abbr, nr = self._getAbbreviationAndNumber(thecomic)
               isAnnual = False
               annualmatch = re.search('@2?$', abbr)
               if annualmatch:
                  abbr = abbr[:annualmatch.start()]
                  isAnnual = True
               full_name = self._getFullComicName(abbr, nr, isAnnual)
               self._anomalyDetector(thecomic, abbr, nr, fig_name, anomalies)
               addComic(thecomic, full_name)
               current['comics'].append(dict(comicstr=thecomic, appendix=theappendix, comicid=comic_dict[thecomic]['id']))
               addAppendix(thecomic, theappendix, fig_index, previous, rawstr, i, current)
               
         if previous:
            for prevcomic in previous['comics']:
               setNext(prevcomic['comicstr'], prevcomic['appendix'], fig_index, current, i)
               
         previous = current
               
      fig_search = ', '.join(extra_search)
      
      return fig_search
      
   def _clean(self, rawstr, isComic=True):
      """
      Remove html tags etc from string @rawstr
      
      * rawstr  - A string to clean
      * isComic - Should be True if rawstr is a comic.
                  Figure redirections are extracted (XXX is extracted in for example 'See XXX' and 'From XXX')
                  and some extra comic specific cleaning is done.
      
      Return clean string, figure redirect string
      """
      
      # Remove html tags
      cleanstr = self.re_tag.sub('',rawstr)
      
      replacements = {"&lt;":"<", "&gt;":">", "&amp;":"&", "&quot;":'"', "&and;":"&", "&Ntilde;":"Ñ", '\n':'', '&hearts;':'HEART'}
      
      # Replace html entities etc
      for torepl,repl in replacements.items():
         cleanstr = cleanstr.replace(torepl,repl)
      rawstr = re.sub(' +', ' ', cleanstr.strip())
      
      figure_redirect = ''
      if isComic:
         cleanstr = self.re_cf.sub('',cleanstr)
         extra_repl = {" | ":" ~ ", " & ":" ~ ", "=":" ~ "}
         for torepl,repl in extra_repl.items():
            cleanstr = cleanstr.replace(torepl,repl)
            
         cleanstr = self.re_to_remove.sub('',cleanstr)
         for r in self.figure_redirections:
            i = cleanstr.find(r)
            if i != -1:
               figure_redirect = cleanstr[i:] + figure_redirect
               cleanstr = cleanstr[:i]
      
         cleanstr = cleanstr.strip()
         cleanstr = re.sub(' +', ' ', cleanstr)
         comics = cleanstr.split(" ~ ")
         
         return comics, rawstr, figure_redirect
         
      return rawstr
      
   def _getComicAndAppendix(self, comicstr):
      """
      Split comic and comic appendix (for example -FB and -BTS)
      Example:
      'A 256-FB' >> ('A 256', '-FB')
      """
      cands = []
      for a in self.comic_appendixes:
         i = comicstr.find(a)
         if i != -1:
            cands.append(i)
      if cands:
         i = min(cands)
         return comicstr[:i].strip(), comicstr[i:]
      return comicstr, ''
  
   def _getAbbreviationAndNumber(self, comicstr):
      """
      Split comic into abbreviation and number.
      Examples:
      'A 1'   >> ('A', '1')
      'A 1.5  >> ('A', '1.5')
      'A:DV'  >> ('A:DV', None)
      'A@ 1'  >> ('A@', '1')
      'A '98' >> ('A', "'98")
      """
      m = self.re_abbr_nr.match(comicstr)
      if not m:
         return comicstr,None
      return m.group('abbr'),m.group('nr')
