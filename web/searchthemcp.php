<html>

  <link rel="stylesheet" href="autocomplete/AutoComplete.css" media="screen" type="text/css">
  <link rel="stylesheet" href="searchthemcp.css" media="screen" type="text/css">
  <link rel="StyleSheet" href="mcp.css" type="text/css">
  <script language="javascript" type="text/javascript" src="autocomplete/autocomplete.js"></script>
  <script language="javascript" type="text/javascript" src="autocomplete/comicsAutoComplete.js"></script>

<head><title>Marvel Chronology Project - Search</title></head>

<body  bgcolor="#ffffff" >

<CENTER>
<SCRIPT LANGUAGE="JavaScript">
<!-- This script and many more are available free online at -->
<!-- The JavaScript Source!! http://javascript.internet.com -->
<!-- Begin
if (window != top) top.location.href = location.href;
// End -->
</SCRIPT>
</CENTER>

<table border="0" width="100%" cellspacing="3"  cellpadding="8" >
<tr>
<td width="15%" valign="top" background="marb015.jpg" bgcolor="#008000">

<div class="leftmenu">
<?php include("menu.php"); ?>
</div>

</td>


<td valign=top width="85%">
<center>

<script type="text/javascript"><!--
google_ad_client = "ca-pub-8198841361942424";
/* standard */
google_ad_slot = "1089191127";
google_ad_width = 728;
google_ad_height = 90;
//-->
</script>
<script type="text/javascript"
src="http://pagead2.googlesyndication.com/pagead/show_ads.js">
</script>




<p>
<a href="index.htm"><img src="mcpbannr.gif" alt="Home" border="0" width="439" height="65"></a><br>
<h1>Search</h1>
</center>

<hr>
<a href="index.htm"><img src="uparr.gif" alt="[Home]"></a> <a href="key.php"><img src="key.gif" alt="[Key]"></a>
<hr>

Search for characters:
<FORM METHOD="get" ACTION="searchthemcp.php">
<INPUT TYPE="text" SIZE="20" NAME="searchForCharacters">
<INPUT TYPE="submit" VALUE="Search">
</FORM>
Go to comic:
<FORM ID="comicform" METHOD="get" NAME="gocomic" ACTION="searchthemcp.php">
<INPUT TYPE="text" SIZE="20" NAME="searchForComic" ID="comic" VALUE=""/>
<INPUT TYPE="submit" VALUE="Go">
</FORM>

<script language="javascript" type="text/javascript">
<!--
    function matchfunc(query, comicdict) {
        query = query.toUpperCase();
        var l = comicdict[query];
        if (typeof(l) == "string") {
            query = comicdict[query];
            l = comicdict[query];
        }
        if (l === undefined) {
            return l;
        }
        var matches = new Array();
        for (i=0; i<l.length; ++i) {
            matches[matches.length] = query+l[i];
        }
        return matches;
    }

//    remove the double-slash from the next line to reactivate autocomplete functionality
    AutoComplete_Create('comic', 'comicform', comics, matchfunc, 10);
// -->
</script>

<?php
$figure = $_GET["figure"];
$searchForFigures = $_GET["searchForCharacters"];
$searchForComic = $_GET["searchForComic"];
$comic = $_GET["comic"];
include("mcpfunctions.php");
if($figure != NULL)
   getFigure($figure);
elseif($searchForFigures != NULL)
   searchForFigures($searchForFigures);
elseif($searchForComic != NULL)
   searchForComic($searchForComic);
elseif($comic != NULL)
   getComic($comic)
?>

<hr>
<P>Last updated <I>Saturday, August 15, 2015</I>.</P>

<p>If you're searching for a character or comic with an apostrophe, place a backslash in front of the apostrophe (T\'CHALLA).</p>

<p><B>Search for characters functionality</B><br>
<ul>
<li>
The search query is matched against the character name and the redirections to other characters (for example "See XXX"). Because of this a search for SPIDER-MAN will also match for example RICOCHET II.
</li>
</ul>
</p>

<p>
<B>Go to comic functionality</B><br>
<ul>
<li>
An autocompletion list of available comics will appear if there aren't too many matches. "A 1" will not produce an autocompletion list because it matches all A 100-199, but "A 10" will produce the list A 10, A 101-109.
</li>
<li>
A character appearance is presented with these columns:
<ul>
<li>Name</li>
<li>Previous entry in the character's chronological list</li>
<li>Current row number in the chronological list</li>
<li>Current entry in the chronological list</li>
<li>Next entry</li>
</ul>
</li>
<li>
When clicking on a previous or next comic link, the browser will jump to the corresponding row on the resulting comic page. This is especially useful when jumping between two very intermeshed comics, for example A 16 and M/H&L '97.
</li>
<li>
If the same comic appears more than one time in a character's chronological list, the character will get one row for each appearance. See for example SPIDER-MAN in UTSM 22.
</li>
</ul>
</p>
<hr>
The search was made by <A HREF="mailto:jimmy.petersson@chronologygraph.com">Jimmy Petersson</A><BR>
<A HREF="http://www.chronologygraph.com">www.chronologygraph.com</A>
<hr>
<a href="index.htm"><img src="uparr.gif" alt="[Home]"></a> <a href="key.php"><img src="key.gif" alt=["Key"]></a>
<hr>
<font size="-1">The image of Uatu and all character names on this page are trademarked Marvel Characters, and used without permission.</font>

</td>
</tr>
</table>

</body>

</html>
