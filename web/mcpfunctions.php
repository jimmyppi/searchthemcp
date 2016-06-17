<?php

function openConnection() {
   $host = "localhost";
   $login = "YOUR_MYSQL_USERNAME";
   $dbname = "THE_DATABASE_NAME";
   $password = "YOUR_MYSQL_PASSWORD";
   $db = mysqli_connect($host, $login, $password, $dbname) or errorManagement();
   return $db;
}

function errorManagement($db = "") {
   if (!empty($db)) {
      if ($db->connect_errno) {
         echo "<p>Failed to connect to MySQL: ({$db->connect_errno}){$db->connect_error}</p>";
      }
   }
   echo "<p><a href=\"javascript:history.go(-1)\">Back</a><p>";
   exit();
}

function searchForComic($comic) {
   $db = openConnection();
   $comic = $db->real_escape_string($comic);
   $sql = "SELECT * FROM mcp_comics WHERE abbreviation='{$comic}' ORDER BY appendix,figid,entry_index";
   $result = $db->query($sql) or errorManagement($db);
   publishComic($result, $db);
   $result->close();
   $db->close();
}

function searchForFigures($searchString) {
   $db = openConnection();
   $searchString = $db->real_escape_string($searchString);
   $sql = "SELECT name,link,dimension FROM mcp_figures WHERE search_name LIKE '%{$searchString}%' OR name LIKE '%{$searchString}%'";
   $result = $db->query($sql) or errorManagement($db);
   echo "<p>Results for '{$searchString}':</p>";
   while($figureobj = $result->fetch_object()) {
      if($figureobj->dimension != "standard") {
         echo "<a href=\"{$figureobj->link}\">{$figureobj->name} ({$figureobj->dimension})</a><br>";
      }
      else {
         echo "<a href=\"{$figureobj->link}\">{$figureobj->name}</a><br>";
      }
   }
   $result->close();
   $db->close();
}

function getFigure($index) {
   $db = openConnection();
   $index = $db->real_escape_string($index);
   $sql = "SELECT * FROM figures3 WHERE ind IN ({$index})";
   $result = $db->query($sql) or errorManagement($db);
   if($figureobj = $result->fetch_object()) {
      echo str_replace("\'", "\"", $figureobj->html);
      echo str_replace("\'", "\"", "{$figureobj->list}</b>");
   }
   else
      echo "Could not find the figure.<br>";
   echo "<p>";
   $result->close();
   $db->close();
}

function getComic($index) {
   $db = openConnection();
   $index = $db->real_escape_string($index);
   $sql = "SELECT * FROM mcp_comics WHERE comicid='{$index}' ORDER BY appendix,figid,entry_index";
   $result = $db->query($sql) or errorManagement($db);
   publishComic($result, $db);
   $result->close();
   $db->close();
}

function addLinksToRaw($comicobj, $rawstr, $comics, $linkCurrent) {
   if ($rawstr == "") {
      return "&nbsp;";
   }
   $linkstr = $rawstr;
   for ( $c = 0; $c < sizeof($comics); $c += 1) {
      $ca = split("\\|", $comics[$c]);
      if (!($ca[0] == $comicobj->abbreviation && $ca[2] == $comicobj->appendix && ! $linkCurrent)) {
         $linkstr = str_replace($ca[0], "<a href=\"?comic={$ca[1]}#{$ca[2]}{$comicobj->figid}\">{$ca[0]}</a>", $linkstr);
      }
   }
   return $linkstr;
}

function publishComic($comic, $db) {

   $comicFound = false;
   $current_appendix = -1;
   $color = false;
   while($comicobj = $comic->fetch_object()) {
      if (!$comicFound) {
         $comicFound = true;
         echo "<table class=\"comictable\" cellspacing=0 cellpadding=4><tr><th></th><th>Previous</th><th colspan=2>Current</th><th>Next</th></tr>";
         $comicid = $db->real_escape_string($comicobj->comicid);
         $sql = "SELECT full_name FROM mcp_comics_fullname WHERE comicid='{$comicid}'";
         $result = $db->query($sql) or errorManagement($db);
         if($fullname = $result->fetch_object()) {
            echo "<b>{$fullname->full_name}</b>";
         }
         $result->close();
      }
      if( $comicobj->appendix != $current_appendix ) {
         if ($current_appendix != -1) {
             echo "<tr class=\"space_row\"><td colspan=5>&nbsp;</td></tr>";
         }
         $current_appendix = $comicobj->appendix;
         $color = false;
         echo "<tr id=\"{$current_appendix}\" class=\"comic_title_row\"><td><b>{$comicobj->abbreviation} {$comicobj->appendix}</b></td><td colspan=4>&nbsp;</td></tr>";
      }

      if( $color ) {
              echo "<tr id=\"{$current_appendix}{$comicobj->figid}\" class=\"color_row figrow\">";
      }
      else {
        echo "<tr id=\"{$current_appendix}{$comicobj->figid}\" class=\"figrow\">";
      }
      $figid = $db->real_escape_string($comicobj->figid);
      $sql = "SELECT name,link,dimension FROM mcp_figures WHERE figid='{$figid}'";
      $figresult = $db->query($sql) or errorManagement($db);
      if($figureobj = $figresult->fetch_object()) {
         if($figureobj->dimension != "standard") {
            echo "<td><a href=\"{$figureobj->link}\">{$figureobj->name} ({$figureobj->dimension})</a></td>";
         }
         else {
            echo "<td><a href=\"{$figureobj->link}\">{$figureobj->name}</a></td>";
         }
      }
      $figresult->close();

      $prev_str = addLinksToRaw($comicobj, $comicobj->previous_raw, split("#", $comicobj->previous_comics), true);
      echo "<td>{$prev_str}</td>";

      $current_str = addLinksToRaw($comicobj, $comicobj->current_raw, split("#", $comicobj->current_comics), false);
	  $entryindplus = $comicobj->entry_index+1;
	  echo "<td alight=\"right\">{$entryindplus}</td><td>{$current_str}</td>";

      $next_str = addLinksToRaw($comicobj, $comicobj->next_raw, split("#", $comicobj->next_comics), true);
      echo "<td>{$next_str}</td>";

      $color = !$color;

   }
   if(!$comicFound) {
      echo "<table><tr><td>Could not find the comic.</td></tr>";
   }
   echo "</table>";

}

?>
