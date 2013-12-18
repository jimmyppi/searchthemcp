<?php

function openConnection() {
   $host = "localhost";
   $login= "YOUR_MYSQL_USERNAME";
   $dbname = "THE_DATABASE_NAME";
   $password= "YOUR_MYSQL_PASSWORD";
   $db = mysql_connect($host,$login,$password) or errorManagement();
   mysql_select_db($dbname);
   return $db;
}

function errorManagement($error = "") {
   if (empty($error)) {
      $mysqlError = mysql_error();
      if (!empty($mysqlError)) {
         echo "Error: ".$mysqlError;
      }
   }
   else
      echo "Error: ".$error;
   echo "<br><a href=\"javascript:history.go(-1)\">Back</a><br>";
   exit;
}

function searchForComic($comic) {
   $db = openConnection() or errorManagement();
   $sql = "SELECT * FROM mcp_comics WHERE abbreviation='".$comic."' ORDER BY appendix,figid,entry_index";
   $result = mysql_query($sql,$db) or errorManagement();
   publishComic($result, $db);
   mysql_free_result($result);
}

function searchForFigures($searchString) {
   $db = openConnection() or errorManagement();
   $sql = "SELECT name,link,dimension FROM mcp_figures WHERE search_name LIKE '%".$searchString."%' OR name LIKE '%".$searchString."%'";
   $result = mysql_query($sql, $db) or errorManagement();
   echo "Results for '$searchString':<P>";
   while($figureobj = mysql_fetch_object($result)) {
      if($figureobj->dimension != "standard") {
         echo "<A HREF=\"".$figureobj->link."\">".$figureobj->name." (".$figureobj->dimension.")</A><BR>";
      }
      else {
         echo "<A HREF=\"".$figureobj->link."\">".$figureobj->name."</A><BR>";
      }
   }
   mysql_free_result($result);
}

function getFigure($index) {
   $db = openConnection() or errorManagement();
   $sql = "SELECT * FROM figures3 WHERE ind IN (".$index.")";
   $result = mysql_query($sql, $db) or errorManagement();
   if($figureobj = mysql_fetch_object($result)) {
      echo str_replace("\'", "\"", $figureobj->html);
      echo str_replace("\'", "\"", $figureobj->list)."</b>";
   }
   else
      echo "Could not find the figure.<BR>";
   echo "<P>";
   mysql_free_result($result);
}

function getComic($index) {
   $db = openConnection() or errorManagement();
   $sql = "SELECT * FROM mcp_comics WHERE comicid='".$index."' ORDER BY appendix,figid,entry_index";
   $result = mysql_query($sql,$db) or errorManagement();
   publishComic($result, $db);
   mysql_free_result($result);
}

function addLinksToRaw($comicobj, $rawstr, $comics, $linkCurrent) {
   if ($rawstr == "") {
      return "&nbsp;";
   }
   $linkstr = $rawstr;
   for ( $c = 0; $c < sizeof($comics); $c += 1) {
      $ca = split("\\|", $comics[$c]);
      if (!($ca[0] == $comicobj->abbreviation && $ca[2] == $comicobj->appendix && ! $linkCurrent)) {
         $linkstr = str_replace($ca[0], "<A HREF=\"?comic=".$ca[1]."#".$ca[2]."".$comicobj->figid."\">".$ca[0]."</a>", $linkstr);
      }
   }
   return $linkstr;
}

function publishComic($comic, $db) {

   $comicFound = false;
   $current_appendix = -1;
   $color = false;
   while($comicobj = mysql_fetch_object($comic)) {
      if (!$comicFound) {
         $comicFound = true;
         echo "<TABLE CLASS=\"comictable\" cellspacing=0 cellpadding=4><TR><TH></TH><TH>Previous</TH><TH COLSPAN=2>Current</TH><TH>Next</TH></TR>";
         $sql = "SELECT full_name FROM mcp_comics_fullname WHERE comicid='".$comicobj->comicid."'";
         $result = mysql_query($sql,$db) or errorManagement();
         if($fullname = mysql_fetch_object($result)) {
            echo "<B>".$fullname->full_name."</B>";
         }
         mysql_free_result($result);
      }
      if( $comicobj->appendix != $current_appendix ) {
         if ($current_appendix != -1) {
             echo "<TR CLASS=\"space_row\"><TD COLSPAN=5>&nbsp;</TD></TR>";
         }
         $current_appendix = $comicobj->appendix;
         $color = false;
         echo "<TR ID=\"".$current_appendix."\" CLASS=\"comic_title_row\"><TD><B>".$comicobj->abbreviation." ".$comicobj->appendix."</B></TD><TD COLSPAN=4>&nbsp;</TD></TR>";
      }

      if( $color ) {
      	echo "<TR ID=\"".$current_appendix."".$comicobj->figid."\" CLASS=\"color_row figrow\">";
      }
      else {
        echo "<TR ID=\"".$current_appendix."".$comicobj->figid."\" CLASS=\"figrow\">";
      }

      $sql = "SELECT name,link,dimension FROM mcp_figures WHERE figid='".$comicobj->figid."'";
      $figresult = mysql_query($sql,$db) or errorManagement();
      if($figureobj = mysql_fetch_object($figresult)) {
         if($figureobj->dimension != "standard") {
            echo "<TD><A HREF=\"".$figureobj->link."\">".$figureobj->name." (".$figureobj->dimension.")</A></TD>";
         }
         else {
            echo "<TD><A HREF=\"".$figureobj->link."\">".$figureobj->name."</A></TD>";
         }
      }
      mysql_free_result($figresult);

      $prev_str = addLinksToRaw($comicobj, $comicobj->previous_raw, split("#", $comicobj->previous_comics), true);
      echo "<TD>".$prev_str."</TD>";

      $current_str = addLinksToRaw($comicobj, $comicobj->current_raw, split("#", $comicobj->current_comics), false);
      echo "<TD ALIGN=\"right\">".($comicobj->entry_index+1)."</TD><TD>".$current_str."</TD>";

      $next_str = addLinksToRaw($comicobj, $comicobj->next_raw, split("#", $comicobj->next_comics), true);
      echo "<TD>".$next_str."</TD>";

      $color = !$color;

   }
   if(!$comicFound) {
      echo "Could not find the comic.<BR>";
   }
   echo "</TABLE>";

}

?>
