var BASE_SCRIPT_URL = '/';
//var resCategories = new Array('Creature Food','Creature Structural','Flora Food','Flora Structural','Chemical','Water','Mineral','Gas','Energy');
var defaultGalaxy = 14;
var refreshPos = 0;
var newRecipeID = 0;
var resCategoryIDs = new Array('creature_food','creature_structural','flora_food','flora_structural','chemical','water','mineral','gas','energy_renewable');

function getQueryVar(qsvar) {
  var query = window.location.search.substring(1);
  var vars = query.split("&");
  for (var i=0;i<vars.length;i++) {
    var pair = vars[i].split("=");
    if (pair[0] == qsvar) {
      return pair[1];
    }
  }
  return -1;
}
function markUnavailable(linkFrom, resName, galaxy, planet) {
    var doit = false;
    if (planet == "all")
        doit = confirm("Do you really want to mark "+resName+" unavailable on all planets?");
    else
        doit = true;

    if (doit) {
        $.get(BASE_SCRIPT_URL + "markUnavailable.py", {spawn: resName, galaxy: galaxy, planets: planet, rid: new Date()}, function(data) {
	    if (data.indexOf("Error:")>-1) {
	        alert(data);
	    } else {
	        //alert(data);
			$("#cont_"+resName).empty();
	        $("#cont_"+resName).css("display","none");
	    }
	});
    }
}
function verifyResource(spawnName, onPlanet) {
	// verify resource on specific planet and replace verify container with check indicator
	$.post(BASE_SCRIPT_URL + "postResource.py", { galaxy: $("#galaxySel option:selected").val(), planet: onPlanet, resName: spawnName, forceOp: "verify" },
		function(data) {
			var result = $(data).find("resultText").eq(0).text();
			if (result.indexOf("Error:") == -1) {
				var spawn = $(data).find("spawnName").eq(0).text();
				$("#cont_"+data).fadeOut(300);
				$("#cont_verify_"+spawn).html('<img src="/images/checkGreen16.png" alt="Verified" title="Verified"><span style="vertical-align:4px;"></span>');
				$("#cont_"+data).fadeIn(300);
			} else {
				alert(result);
			}
			$("#resAddResults").append(result+"<br />");
		});
}
function editStats(linkFrom, resName) {
    quickAdd(linkFrom, resName);
}
// Check if old resource needs to be marked unavailable for single instance spawn types
function removeOldCheck(spawnName) {
	$.get(BASE_SCRIPT_URL + "checkOldResource.py", { galaxy: $("#galaxySel option:selected").val(), spawn: spawnName },
			function(data) {
				var result = $(data).find("resultText").eq(0).text();
				if (result == "found") {
					var oldID = $(data).find("oldSpawnID").eq(0).text();
					var oldName = $(data).find("oldSpawnName").eq(0).text();
					var newName = $(data).find("spawnName").eq(0).text();
					var resType = $(data).find("resourceType").eq(0).text();
					var resAge = $(data).find("resAge").eq(0).text();
					var doit = false;
					doit = confirm("I found an old resource entered " + resAge + " ago - " + oldName + ", of the same type as the " + resType + " " + newName + " that you are adding.\n\nNormally only one of this type of resource is in spawn at a time.\n\nDo you want to mark the old resource unavailable now?");
					if (doit) {
						$.get(BASE_SCRIPT_URL + "markUnavailable.py", {spawn: oldName, galaxy: $("#galaxySel option:selected").val(), planets: "all", rid: new Date()}, function(data) {
	    					if (data.indexOf("Error:")>-1) {
	        					alert(data);
	    					} else {
	        					$("#cont_"+data).css("display","none");
	    					}
						});
					}
				}
			}, "xml");
}
// sends resource data to be posted from the addResource page
function postResources(linkappend) {
	resStr = "";
	numReturns = 0;
	numRes = 0;
	if ($("#planetSel option:selected").val() == 0) {
		alert("Select a planet first please.");
	} else {
		$("#resMask").css("display","block");
		for (x=0;x<rownum;x++) {
			tmpNameBox = document.getElementById("resName"+x);
			resStr = tmpNameBox.value.toLowerCase();
			if (resStr != "") {
				numRes += 1;
				$.post(BASE_SCRIPT_URL + "postResource.py?" + linkappend, { galaxy: $("#galaxySel option:selected").val(), planet: $("#planetSel option:selected").val(), resName: resStr, resType: $("#typeSel"+x+" option:selected").val(), sourceRow: x, CR: $("#CR"+x).val(), CD: $("#CD"+x).val(), DR: $("#DR"+x).val(), FL: $("#FL"+x).val(), HR: $("#HR"+x).val(), MA: $("#MA"+x).val(), PE: $("#PE"+x).val(), OQ: $("#OQ"+x).val(), SR: $("#SR"+x).val(), UT: $("#UT"+x).val(), ER: $("#ER"+x).val() },
					function(data) {
						var result = $(data).find('resultText').eq(0).text();
						var spawnName = $(data).find("spawnName").eq(0).text();
						var sr = $(data).find("sourceRow").eq(0).text();
						//$("#addInfo"+sr).html(result);
						$("#resMask").append(result+"<br />");
						numReturns += 1;
						$("#resMask").css("color","grey");
						$("#resMask").css("color","white");
						// check for old resource of same type for single instance spawn type
						if (result.indexOf("Error:") == -1) {
							removeOldCheck(spawnName);
						}
						if (numReturns >= numRes)
							$("#sentMessage").html("<span class='standOut'>All resources posted!</span><a class='bigLink' href='addResources.py'>Add More</a>");
					}, "xml");
			}
		}
		return false;
	}
}
// send resources to be posted from quick add on home page
var newPos = 0; // current index of new resources being entered data for
var newNames = new Array();
var newTypes = new Array();
var newMsg = new Array();
var numReturns = 0; // total number of results from resource lookups returned
var numRes = 0; // total number of resources entered
function quickAdd(qform, singleName) {
	var resStr = "";
	if (singleName != "") resStr = singleName;
	else resStr = qform.resName.value.toLowerCase();
	var textLen = resStr.length;
	var resNames = new Array();
	var regex=/^[A-Za-z]+$/;
	var notRes = 1;
	var thisRes = "";
	var i = 0;
	var newTemp = 0;

	newPos = 0;
	newNames = new Array();
	newTypes = new Array();
	newMsg = new Array();
	numReturns = 0;
	numRes = 0;

	if ($("#planetSel option:selected").val() < 1 || $("#planetSel option:selected").val() == "any") {
		if (singleName == "") {
			alert("Select a planet first please.");
			return false;
		} else {
			if (qform == null) {
				alert("Select a planet in the search criteria box first to verify this resource on that planet.");
				return false;
			}
		}
	}

	for (i=0;i<textLen;i++) {
		if (regex.test(resStr.substr(i,1))) {
			if (notRes) {
				if (thisRes != "") {
					resNames[numRes] = thisRes;
					numRes += 1;
					thisRes = "";
				}
			}
			thisRes += resStr.substr(i,1);
			notRes = 0;
		} else {
			notRes = 1;
		}
	}
	if (thisRes != "") {
		resNames[numRes] = thisRes;
		numRes +=1;
	}
	if (numRes > 0) {
		$("#resAddResults").html("");
		showWindow("#resourceDialog");
	} else {
		alert("No valid resource names entered.");
	}
	$("#addBusyImg").css("display", "block");
	for (i=0;i<numRes;i++) {
		$("#resStatusUpdate").html("Searching for stats for " + resNames[i] + "<br/>");
		$.get(BASE_SCRIPT_URL + "getResourceByName.py", { name: resNames[i], galaxy: $("#galaxySel option:selected").val(), rid: new Date() },
			function(data) {
				var result = $(data).find("resultText").eq(0).text();
				var spawnName = $(data).find("spawnName").eq(0).text();
				if (result.substr(0,6) == "Error:") {
					$("#resAddResults").append(result+"<br />");
					$("#resourceDialog").css("height", $(winId).height()+24);
				} else {
					var regNums=/\d/;
					var spawnID = $(data).find("spawnID").eq(0).text();
					var resourceType = $(data).find("resourceType").eq(0).text();
					var CR = $(data).find("CR").eq(0).text();
					var CD = $(data).find("CD").eq(0).text();
					var DR = $(data).find("DR").eq(0).text();
					var FL = $(data).find("FL").eq(0).text();
					var HR = $(data).find("HR").eq(0).text();
					var MA = $(data).find("MA").eq(0).text();
					var PE = $(data).find("PE").eq(0).text();
					var OQ = $(data).find("OQ").eq(0).text();
					var SR = $(data).find("SR").eq(0).text();
					var UT = $(data).find("UT").eq(0).text();
					var ER = $(data).find("ER").eq(0).text();
					if (spawnID) {
						if (regNums.test(CR+CD+DR+FL+HR+MA+PE+OQ+SR+UT+ER)) {
							if (singleName == "" || qform == null) {
								if (qform == null) {
									// verify resource
									$.post(BASE_SCRIPT_URL + "postResource.py", { galaxy: $("#galaxySel option:selected").val(), planet: $("#planetSel option:selected").val(), resID: spawnID, forceOp: "verify" },
										function(data) {
											var result = $(data).find("resultText").eq(0).text();
											if (result.indexOf("Error:") == -1) {
												var spawn = $(data).find("spawnName").eq(0).text();
												$("#cont_"+data).fadeOut(300);
												$("#cont_verify_"+spawn).html('<img src="/images/checkGreen16.png" alt="Verified" title="Verified"><span style="vertical-align:4px;">by you just now!</span>');
												$("#cont_"+data).fadeIn(300);
												//$(linkFrom).addClass(planetName.replace(' ',''));
												//$(linkFrom).click("planetRemove(this,"+planet+","+spawn+",'"+planetName+"');");
											} else {
												//alert(result);
											}
											$("#resAddResults").append(result+"<br />");
										});
								} else {
									// existing stats and new entry post resource to planet or verify
									$.post(BASE_SCRIPT_URL + "postResource.py", { galaxy: $("#galaxySel option:selected").val(), planet: $("#planetSel option:selected").val(), resID: spawnID },
										function(data) {
											var result = $(data).find("resultText").eq(0).text();
											$("#resAddResults").append(result+"<br />");
											$("#resourceDialog").css("height", $("#resourceDialog").height()+14);
										});
								}
							} else {
								// when single name populated a direct edit of resource was initiated
								newTemp = newNames.length;
								newNames[newTemp] = spawnName;
								newTypes[newTemp] = resourceType;
								newMsg[newTemp] = "Editing: <span class='tableHead'>" + spawnName + "</span> has been entered, and has stats, please edit if they are wrong.";
								CR: $("#CR0").val(CR);
								CD: $("#CD0").val(CD);
								DR: $("#DR0").val(DR);
								FL: $("#FL0").val(FL);
								HR: $("#HR0").val(HR);
								MA: $("#MA0").val(MA);
								PE: $("#PE0").val(PE);
								OQ: $("#OQ0").val(OQ);
								SR: $("#SR0").val(SR);
								UT: $("#UT0").val(UT);
								ER: $("#ER0").val(ER);
							}
						} else {
							// no existing stats
							if (singleName != "") {
								// when single name populated a direct edit of resource was initiated
								newTemp = newNames.length;
								newNames[newTemp] = spawnName;
								newTypes[newTemp] = resourceType;
								newMsg[newTemp] = "Editing: <span class='tableHead'>"+spawnName+"</span> has been entered, but it does not have stats.";
								// Clear the form incase values were in from a previous edit
								CR: $("#CR0").val("");
								CD: $("#CD0").val("");
								DR: $("#DR0").val("");
								FL: $("#FL0").val("");
								HR: $("#HR0").val("");
								MA: $("#MA0").val("");
								PE: $("#PE0").val("");
								OQ: $("#OQ0").val("");
								SR: $("#SR0").val("");
								UT: $("#UT0").val("");
								ER: $("#ER0").val("");
							} else {
								// existing resource with no stats entered
								newTemp = newNames.length;
								newNames[newTemp] = spawnName;
								newTypes[newTemp] = resourceType;
								newMsg[newTemp] = "<span class='tableHead'>" + spawnName + "</span> has been entered, but I dont have stats on it.";
								// Clear the form incase values were in from a previous edit
								CR: $("#CR0").val("");
								CD: $("#CD0").val("");
								DR: $("#DR0").val("");
								FL: $("#FL0").val("");
								HR: $("#HR0").val("");
								MA: $("#MA0").val("");
								PE: $("#PE0").val("");
								OQ: $("#OQ0").val("");
								SR: $("#SR0").val("");
								UT: $("#UT0").val("");
								ER: $("#ER0").val("");
							}
						}
					} else {
						// completely new resource
						newTemp = newNames.length;
						newNames[newTemp] = spawnName;
						newTypes[newTemp] = resourceType;
						newMsg[newTemp] = "I dont have any information on <span class='tableHead'>" + spawnName + "</span>.  Please enter resource info.";
					}
				}
				// check if we're ready to add data for first resource after first result returns
				if (numReturns==0) {
					numReturns += 1;
					quickAddNext();
				} else {
					numReturns += 1;
				}
				if (numReturns >= numRes)
					$("#resStatusUpdate").html("Lookups complete.");
			}, "xml");
	}
}
// save info added to form for prompted resource
function quickAddSave() {
	var typeSel = $("#typeSel option:selected").val();
	if (typeSel == "none") {
		alert("You can't save a resource without selecting a type.");
	} else {
		if (newNames[newPos-1] != "") {
			if (newMsg[newPos-1].substr(0,8) == "Editing:") {
				// post resource by editing resource details only
				$.post(BASE_SCRIPT_URL + "postResource.py?forceOp=edit", {galaxy: $("#galaxySel option:selected").val(),
					resName: newNames[newPos-1],
					forceOp: "edit",
					resType: $("#typeSel option:selected").val(),
					CR: $("#CR0").val(),
					CD: $("#CD0").val(),
					DR: $("#DR0").val(),
					FL: $("#FL0").val(),
					HR: $("#HR0").val(),
					MA: $("#MA0").val(),
					PE: $("#PE0").val(),
					OQ: $("#OQ0").val(),
					SR: $("#SR0").val(),
					UT: $("#UT0").val(),
					ER: $("#ER0").val() },
					function(data) {
						var result = $(data).find("resultText").eq(0).text();
						$("#resAddResults").append(result+"<br />");
					}, "xml");
			} else {
				// post all resource data collected
				$.post(BASE_SCRIPT_URL + "postResource.py", { galaxy: $("#galaxySel option:selected").val(), planet: $("#planetSel option:selected").val(), resName: newNames[newPos-1], resType: $("#typeSel option:selected").val(), CR: $("#CR0").val(), CD: $("#CD0").val(), DR: $("#DR0").val(), FL: $("#FL0").val(), HR: $("#HR0").val(), MA: $("#MA0").val(), PE: $("#PE0").val(), OQ: $("#OQ0").val(), SR: $("#SR0").val(), UT: $("#UT0").val(), ER: $("#ER0").val() },
					function(data) {
						var result = $(data).find("resultText").eq(0).text();
						var spawnName = $(data).find("spawnName").eq(0).text();
						$("#resAddResults").append(result+"<br />");
						$("#resourceDialog").css("height", $("#resourceDialog").height()+24);
						// Check if old resource needs to be marked unavailable for single instance spawn types
						if (result.indexOf("Error:") == -1) {
							removeOldCheck(spawnName);
						}
					}, "xml");
			}
		}
		// after valid input sent, move to next resource
		quickAddNext();
	}
}
function quickAddNext() {
	// if we havent reached end of new resources to enter, prompt for info
	// otherwise check if we need to wait for results
	if (newPos < newNames.length) {
		$("#addBusyImg").css("display", "none");
		$("#typeSel").removeAttr("disabled");
		if (newTypes[newPos].length > 0) {
			$("#typeSel").val(newTypes[newPos]);
			// pre-populate stats when editing
			if (newMsg[newPos].indexOf("Editing:") != -1) {
				maskStats(document.getElementById("typeSel"), false);
			} else {
				maskStats(document.getElementById("typeSel"));
			}
		} else {
			$("#typeSel").val("none");
			maskStats(document.getElementById("typeSel"));
		}
		$("#resCurrentInfo").html(newMsg[newPos]);
		$("#skipRes").removeAttr("disabled");
		$("#saveRes").removeAttr("disabled");
		newPos += 1;
	} else {
		quickAddCheck();
	}
}
function quickAddCheck() {
	// if there are still results to be returned, wait a second and try going to the next one again
	if (numRes > numReturns) {
		$("#addBusyImg").css("display", "block");
		setTimeout('quickAddNext()', 1000);
	} else {
		// lookups are done
		$("#addBusyImg").css("display", "none");
		$("#resStatusUpdate").html("Lookups complete.");
		// check if we have reached end of new resources and shut down if so
		if (newPos >= newNames.length) {
			$("#resCurrentInfo").html("All Done!");
			$("#typeSel").attr("disabled", true);
			$("#saveRes").attr("disabled", true);
			$("#skipRes").attr("disabled", true);
		}
	}
}
function getResource(resNameBox) {
// Look up this resource to see if stats/planets already entered
  if (resNameBox.value.length>1) {
    var boxRow = resNameBox.id.substring(7);
    $("#addInfo"+boxRow).html("Searching...");
    $.get(BASE_SCRIPT_URL + "getResourceByName.py", { name: resNameBox.value, galaxy: $("#galaxySel option:selected").val(), rid: new Date() },
      function(data) {
          var result = $(data).find('resultText').eq(0).text();
          if (result == "new") {
              result = "<img src='/images/circleBlue16.png' title='This resource has not been entered' alt='New' /><span style='vertical-align:4px'>New</span>";
              $("#addInfo"+boxRow).html(result);
          }
          if (result.substr(0,6) == "Error:") {
              alert(result);
          } else {
              var spawnID = $(data).find('spawnID').eq(0).text();
              if (spawnID) {
                  var resourceType = $(data).find('resourceType').eq(0).text();
                  var planets = $(data).find('Planets').eq(0).text();
                  if (result == "found") {
                      result = "<img src='/images/checkGreen16.png' title='This resource has been marked currently available on "+planets+"' alt='Found' /><span style='vertical-align:4px;'>Found</span>";
                      $("#addInfo"+boxRow).html(result);
                  }
                  $("#typeSel"+boxRow).val(resourceType);
                  maskStats(document.getElementById("typeSel"+boxRow));
                  var CR = $(data).find('CR').eq(0).text();
                  if (CR != "None")
                      $("#CR"+boxRow).val(CR);
                  var CD = $(data).find('CD').eq(0).text();
                  if (CD != "None")
                      $("#CD"+boxRow).val(CD);
                  var DR = $(data).find('DR').eq(0).text();
                  if (DR != "None")
                      $("#DR"+boxRow).val(DR);
                  var FL = $(data).find('FL').eq(0).text();
                  if (FL != "None")
                      $("#FL"+boxRow).val(FL);
                  var HR = $(data).find('HR').eq(0).text();
                  if (HR != "None")
                      $("#HR"+boxRow).val(HR);
                  var MA = $(data).find('MA').eq(0).text();
                  if (MA != "None")
                      $("#MA"+boxRow).val(MA);
                  var PE = $(data).find('PE').eq(0).text();
                  if (PE != "None")
                      $("#PE"+boxRow).val(PE);
                  var OQ = $(data).find('OQ').eq(0).text();
                  if (OQ != "None")
                      $("#OQ"+boxRow).val(OQ);
                  var SR = $(data).find('SR').eq(0).text();
                  if (SR != "None")
                      $("#SR"+boxRow).val(SR);
                  var UT = $(data).find('UT').eq(0).text();
                  if (UT != "None")
                      $("#UT"+boxRow).val(UT);
                  var ER = $(data).find('ER').eq(0).text();
                  if (ER != "None")
                      $("#ER"+boxRow).val(ER);
                  $("#resName"+(parseInt(boxRow)+1)).focus();
              }
          }
      }, "xml");
    var stopAdd = false;
    var tmpBox;
    for (x=0;x<rownum;x++) {
      tmpBox = document.getElementById("resName"+x);
      if (tmpBox)
        if (tmpBox.value == "" || (!tmpBox.value))
          stopAdd = true;
    }
    if (!stopAdd) addResourceRow();
  }
}
function getResourceFuzzy(typeBox, boxRow) {
  // Look up other resources of this type with similar names incase of typo
  // only if a type is selected and exact match was not found
  if (typeBox.selectedIndex > 0 && $("#addInfo"+boxRow).html().indexOf("New",0) > 0) {
    $.get(BASE_SCRIPT_URL + "getResourceByTypeAndFuzzyName.py", { name: $("#resName" + boxRow).val(), galaxy: $("#galaxySel option:selected").val(), resType: typeBox.value, rid: new Date() },
      function(data) {
          var result = $(data).find('resultText').eq(0).text();
          if (result.substr(0,6) == "Error:") {
              alert(result);
          }
          if (result == "found") {
              var spawnID = $(data).find('spawnID').eq(0).text();
              if (spawnID) {
                  var spawnName = $(data).find('spawnName').eq(0).text();
                  var planets = $(data).find('Planets').eq(0).text();
                  result = "<img src='/images/checkGreen16.png' title='This resource has been marked currently available on "+planets+"' alt='Found' /><span style='vertical-align:4px;'>Found</span>";
                  doit = confirm("I found a current resource of the same type with almost the same name.  Is the resource you are entering actually " + spawnName + "?");
                  if (doit) {
		              $("#addInfo"+boxRow).html(result);
		              $("#resName"+boxRow).val(spawnName);
		              var CR = $(data).find('CR').eq(0).text();
		              if (CR != "None")
		                  $("#CR"+boxRow).val(CR);
		              var CD = $(data).find('CD').eq(0).text();
		              if (CD != "None")
		                  $("#CD"+boxRow).val(CD);
		              var DR = $(data).find('DR').eq(0).text();
		              if (DR != "None")
		                  $("#DR"+boxRow).val(DR);
		              var FL = $(data).find('FL').eq(0).text();
		              if (FL != "None")
		                  $("#FL"+boxRow).val(FL);
		              var HR = $(data).find('HR').eq(0).text();
		              if (HR != "None")
		                  $("#HR"+boxRow).val(HR);
		              var MA = $(data).find('MA').eq(0).text();
		              if (MA != "None")
		                  $("#MA"+boxRow).val(MA);
		              var PE = $(data).find('PE').eq(0).text();
		              if (PE != "None")
		                  $("#PE"+boxRow).val(PE);
		              var OQ = $(data).find('OQ').eq(0).text();
		              if (OQ != "None")
		                  $("#OQ"+boxRow).val(OQ);
		              var SR = $(data).find('SR').eq(0).text();
		              if (SR != "None")
		                  $("#SR"+boxRow).val(SR);
		              var UT = $(data).find('UT').eq(0).text();
		              if (UT != "None")
		                  $("#UT"+boxRow).val(UT);
		              var ER = $(data).find('ER').eq(0).text();
		              if (ER != "None")
		                  $("#ER"+boxRow).val(ER);
		              $("#resName"+(parseInt(boxRow)+1)).focus();
                  }
              }
          }
      }, "xml");
    var stopAdd = false;
    var tmpBox;
    for (x=0;x<rownum;x++) {
      tmpBox = document.getElementById("resName"+x);
      if (tmpBox)
        if (tmpBox.value == "" || (!tmpBox.value))
          stopAdd = true;
    }
    if (!stopAdd) addResourceRow();
  }
}
function quickSearch(form) {
    window.location.href = BASE_SCRIPT_URL + "resourceList.py?planet="+form.planetSearchSel.value+"&rgroup="+form.resGroup.value+"&rtype="+form.resType.value;
}
function planetAdd(linkFrom, planet, spawn, planetName) {
	var doit = false;
	doit = confirm("Do you want to add this resource to "+planetName+"?");

	if (doit) {
		$.post(BASE_SCRIPT_URL + "changeAvailability.py",{ spawnID: spawn, planets: planet, availability: 1 },
			function(data) {
				if (data.indexOf("Error")>-1) {
					alert(data);
				} else {
					$("#cont_"+data).fadeOut(300);
					$(linkFrom).removeAttr('onclick');
					$(linkFrom).unbind('click');
					$(linkFrom).click(function(){planetRemove(this,planet,spawn,planetName);});
					$(linkFrom).addClass(planetName.replace(' ',''));
					$("#cont_"+data).fadeIn(300);
				}
			}, "html");
	}
}
function planetRemove(linkFrom, planet, spawn, planetName) {
	var doit = false;
	doit = confirm("Do you want to remove this resource from "+planetName+"?");

	if (doit) {
		$.post(BASE_SCRIPT_URL + "changeAvailability.py",{ spawnID: spawn, planets: planet, availability: 0 },
			function(data) {
				if (data.indexOf("Error")>-1) {
					alert(data);
				} else {
					$("#cont_"+data).fadeOut(300);
					$(linkFrom).removeAttr('onclick');
					$(linkFrom).unbind('click');
					$(linkFrom).click(function(){planetAdd(this,planet,spawn,planetName);});
					$(linkFrom).removeClass(planetName.replace(' ',''));
					$("#cont_"+data).fadeIn(300);
				}
			}, "html");
	}

}
function loadPlanetSel(galaxy, optionZero, elmSelector) {
  var planetOptions = optionZero || '';
  var elmSelector = elmSelector || '#planetSel'
  // Fetch planet data and load into html select elm
  $.post(BASE_SCRIPT_URL + "getList.py", { listType: "planet", galaxy: galaxy},
    function(data) {
      var planetIds = $(data).find('planet_values');
      var planetNames = $(data).find('planet_names');
      for (var i=0;i<$(planetIds).find('item').length;i++) {
          planetOptions = planetOptions + '<option value=' + $(planetIds).find('item').eq(i).text() + '>' + $(planetNames).find('item').eq(i).text() + '</option>';
      }
      $(elmSelector).html(planetOptions);
    }, "xml");
  return;
}
function compareResources(resGroup) {
	// Highlight comparisons between galaxy and inventory resource lists
	$("#" + resGroup + " .resourceCompareGroup").each(function() {
		var galaxyResources = $(this).children()[0];
		var myResources = $(this).children()[1];
		for (var i = 0; i < $(galaxyResources).find(".resourceBox").length; i++) {
			if (i < $(myResources).find(".resourceBox").length) {
				galaxyRes = $(galaxyResources).find(".resourceBox")[i];
				myRes = $(myResources).find(".resourceBox")[i];
				galaxyQuality = parseInt($(galaxyRes).attr("title"));
				myQuality = parseInt($(myRes).attr("title"));
				if (galaxyQuality > myQuality) {
					compareInfo = $(galaxyRes).find(".compareInfo")[0];
					if ($(compareInfo).children().length < 2) {
						$(compareInfo).append("<span class='qualityBad'>&nbsp;(" + (((galaxyQuality - myQuality) / myQuality)*100).toFixed(1) + "% better!)</span>");
					}
				}
			}
		}
	});
}

function addFavorite(galaxyID, spawnName) {
	$.post(BASE_SCRIPT_URL + "setFavorite.py",{ galaxy: galaxyID, itemName: spawnName, favType: 1, op: 1 },
		function(data) {
			if (data.substr(0,5) == "Error") {
				alert(data);
			} else {
				filterResources();
			}
		}, "html");
}

function removeFavorite(favoriteItem, itemType) {
	$.post(BASE_SCRIPT_URL + "setFavorite.py",{ itemID: favoriteItem, favType: itemType },
		function(data) {
			if (data.substr(0,5) == "Error") {
				alert(data);
			} else {
				// all good
			}
		}, "html");
}

function favoritePicker(linkFrom, spawnID, galaxyID, spawnName, currentFavInfo) {
	$('#favCurrentInfo').html(`Select favorite group for ${spawnName}`);
	$('#favPicksurvey').unbind('click');
	$('#favPicksurvey').click(function(){updateFavoriteGroup(spawnID, 'Surveying', galaxyID);$(linkFrom).css('background-image', 'url(\'/images/resources/underground_liquid.png\')');favoritePickerCloseRefresh();});
	$('#favPickharvest').unbind('click');
	$('#favPickharvest').click(function(){updateFavoriteGroup(spawnID, 'Harvesting', galaxyID);$(linkFrom).css('background-image', 'url(\'/images/harvesterCapacity.png\')');favoritePickerCloseRefresh();});
	$('#favPickinv').unbind('click');
	$('#favPickinv').click(function(){if (currentFavInfo == '-') {addFavorite(galaxyID, spawnName);} else {updateFavoriteGroup(spawnID, $('#favPickerGroupSel').val(), galaxyID);}$(linkFrom).css('background-image', 'url(\'/images/inventory32.png\')');favoritePickerCloseRefresh();});
	$('#favPickshop').unbind('click');
	$('#favPickshop').click(function(){updateFavoriteGroup(spawnID, 'Shopping', galaxyID);$(linkFrom).css('background-image', 'url(\'/images/favoriteOn.png\')');favoritePickerCloseRefresh();});
	$('#favRemove').unbind('click');
	$('#favRemove').click(function(){removeFavorite(spawnID, 1);$(linkFrom).css('background-image', 'url(\'/images/favSelector.png\')');favoritePickerCloseRefresh();});
	$('#favText'+currentFavInfo).addClass('contrastStyle');
	if (currentFavInfo == '-') {
		$('#favRemove').hide();
		$('#favPickerGroupSel').hide();
	} else {
		$('#favRemove').show();
		$('#favPickerGroupSel').show();
	}
	$("#favPickerGroupSel").load(BASE_SCRIPT_URL + "getMyGroups.py",{favType:1, firstOption: "<option value=\"Incoming\">Incoming</option>", excludeGroups: "system"});
	showWindow("#favoriteDialog");
}

function favoritePickerCloseRefresh() {
	if (window.location.href.includes('ghHome')) {
      refreshSurveying();
      refreshHarvesting();
	}
	$('#mask, .window').hide();
}

function toggleFavorite(linkFrom, favoriteType, favoriteItem, galaxyID) {
	$.post(BASE_SCRIPT_URL + "setFavorite.py",{ itemID: favoriteItem, favType: favoriteType, galaxy: galaxyID },
		function(data) {
			if (data.substr(0,5) == "Error") {
				alert(data);
			} else {
				if (data.indexOf("added") != -1) {
					$(linkFrom).html('<img src="/images/favorite16On.png" />');
				} else if (data.indexOf("removed") != -1) {
					$(linkFrom).html('<img src="/images/favorite16Off.png" />');
				} else {
					// refresh page for group?
				}
			}
		}, "html");
}

function updateFavoriteGroup(spawnID, groupName, galaxyID) {
	$.post(BASE_SCRIPT_URL + "setFavorite.py",{ itemID: spawnID, favType: 1, favGroup: groupName, galaxy: galaxyID },
		function(data) {
			if (data.substr(0,5) == "Error") {
				alert(data);
			} else {
				// all good
			}
		}, "html");
}

function updateFavoriteAmount(linkFrom, spawnID, amt) {
	if ($(linkFrom).attr("tag") != linkFrom.value) {
		// set to zero if they cleared the value
		if (amt == "") {
			amt = "0"
		}
		$.post(BASE_SCRIPT_URL + "setFavorite.py",{ itemID: spawnID, favType: 1, units: amt },
			function(data) {
				if (data.substr(0,5) == "Error") {
					alert(data);
				} else {
					// all good
					$(linkFrom).attr("tag",amt);
					$(linkFrom).css("color","black");
				}
			}, "html");
	}
}

function updateFavoriteAlert(spawnID, despawnAlert, favType, galaxyID) {
	$.post(BASE_SCRIPT_URL + "setFavorite.py",{ itemID: spawnID, favType: favType, despawnAlert: despawnAlert, galaxy: galaxyID },
		function(data) {
			if (data.substr(0,5) == "Error") {
				alert(data);
			} else {
				// all good
			}
		}, "html");
}

/*   Recipe Functions */
function newRecipe(schematicID, recipeName, galaxyID) {
	$('#busyImgAdd').css('display','block');
	$.post(BASE_SCRIPT_URL + "postRecipe.py", { schematic: schematicID, recipeName: recipeName, galaxy: galaxyID },
		function(data) {
			var result = $(data).find('resultText').eq(0).text();
			var newID = $(data).find("recipeID").eq(0).text();
			$('#busyImgAdd').css('display','none');
			if (result.substr(0,5) == "Error") {
				alert(result);
			} else {
				newRecipeID = newID
				$("#mask, .window").hide();
				refreshRecipes(newID);
			}
		}, "xml");
}

function deleteRecipe(linkFrom, recipeID) {
	var doit = false;
	doit = confirm("Are you sure you want to permanently delete this recipe?");

	if (doit) {
		$.post(BASE_SCRIPT_URL + "postRecipe.py", { recipeID: recipeID, op: "delete" },
			function(data) {
				var result = $(data).find('resultText').eq(0).text();
				var newID = $(data).find("recipeID").eq(0).text();
				if (result.substr(0,5) == "Error") {
					alert(result);
				} else {
					if (linkFrom == "recipe") {
						document.location.href=BASE_SCRIPT_URL + "recipe.py/home";
					} else {
						$("#recipe" + recipeID).hide(1200);
					}
				}
			}, "xml");
	}
}

function saveRecipe(recipeID, recipeName) {
	$('#busyImgSave').css('display','block');
	// build comma separated list of ingredient slots and what they are filled with.
	var ingredients = '';
	$('#recipeIngredients').find('div').each(function() {
		var slot = $(this).children('.ingredientSlot')[0];
		if ($(slot).attr('tag') == 'filled') {
			var spawn = $(slot).attr('spawnID');
			var name = $(this).children('.ingredientHeader').text().replace(/ /g,'_');
			ingredients += name + ':' + spawn + ',';
		}
	});
	if (ingredients == '') {
		ingredients = 'clear';
	}
	$.post(BASE_SCRIPT_URL + 'postRecipe.py', { recipeID: recipeID, recipeName: recipeName, ingredients: ingredients },
		function(data) {
			var result = $(data).find('resultText').eq(0).text();
			$('#busyImgSave').css('display','none');
			$('#recipeMessage').hide();
			$('#recipeMessage').html(result);
			$('#recipeMessage').show(1000);
		}, 'xml');
}

function addRecipeIngredient(recipeID, spawnID) {
	$.post(BASE_SCRIPT_URL + 'postRecipe.py', { recipeID: recipeID, spawnID: spawnID, op: 'addspawn' },
		function(data) {
			var result = $(data).find('resultText').eq(0).text();
			if (result.substr(0,5) == "Added") {
				refreshRecipes();
			} else {
				alert(result);
			}
		}, 'xml');
}

function saveSuggestedRecipe(schematicID, recipeName, ingredients, galaxyID) {
	$('#busyImgSave').css('display','block');
	$.post(BASE_SCRIPT_URL + 'postRecipe.py', { schematic: schematicID, recipeName: recipeName, ingredients: ingredients, galaxy: galaxyID },
		function(data) {
			var result = $(data).find('resultText').eq(0).text();
			$('#busyImgSave').css('display','none');
			refreshRecipes();
		}, 'xml');
}

// Populate list of resource totals needed for a factory run based on ingredient slots filled on page.
function getFactoryList(runAmount) {
	result = '';
	if (!isNaN(runAmount)) {
		ings = $('#recipeIngredients').children();
		result = '<ul class="plain">';
		for (var i = 0; i < ings.length; i++) {
			ingType = $(ings[i]).attr('title').substr(9);
			ingTitle = $($(ings[i]).children()[1]).attr('tt');
			ingQuantity = $($(ings[i]).children()[1]).html().split('/')[1];
			if (ingTitle == undefined) {
				result += '<li>' + (ingQuantity * runAmount) + ': ' + ingType + '</li>';
			} else {
				result += '<li>' + (ingQuantity * runAmount) + ': ' + ingTitle.substr(13, ingTitle.indexOf('br')) + '</li>';
			}
		}
		result += '</ul>';
		result += '<button type="button" value="Deduct From Inventory" class="ghButton" style="width:100%;" onclick="deductFromInventory(' + runAmount + ', \'recipeIngredients\')">Deduct From Inventory</button>';
	} else {
		result = 'That is not a valid number';
	}
	$('#factoryResults').html(result);
}
// Automatically reduce user inventory amounts based on recipe run
function deductFromInventory(runAmount, ingredientContainer) {
	result = '';
	$('#busyImgSave').css('display','block');
	if (!isNaN(runAmount)) {
		ings = $('#' + ingredientContainer).children();
		result = '';
		for (var i = 0; i < ings.length; i++) {
			ingTitle = $($(ings[i]).children()[1]).attr('tt');
			ingQuantity = $($(ings[i]).children()[1]).html().split('/')[1];
			if (ingTitle != undefined) {
				result += ',' + ingTitle.substr(13, ingTitle.indexOf(',')-13) + ':' + (ingQuantity * runAmount);
			}
		}
		if (result.length > 0) {
			result = result.substring(1);
			$.post(BASE_SCRIPT_URL + 'updateInventory.py', { galaxy: $('#galaxySel').val(), operation: '-', updateList: result },
				function(data) {
					var result = $(data).find('resultText').eq(0).text();
					$('#busyImgSave').css('display','none');
					$('#recipeMessage').html(result);
					refreshInventory();
				}, 'xml');
		}
	} else {
		result = 'That is not a valid number';
		$('#recipeMessage').html(result);
	}
	$('#busyImgSave').css('display','none');

}

// Return style to use for coloring on resource quality status preview
function getResourceValueColor(resourceValue) {
	if (resourceValue >= 650) {
		return "green";
	} else if (resourceValue >= 350) {
		return "yellow";
	} else {
		return "red";
	}
}

/*   Waypoint Functions */

// Refresh listed and drawn waypoints on map
function refreshWaypoints() {
	var canvas = document.getElementById("mapCanvas");
	// clear canvas and draw waypoints for this planet
	if (canvas.getContext) {
		var context = canvas.getContext("2d");
		context.clearRect(0, 0, 840, 820);
		$("#coords").show();
	}
	drawWaypoints(mapPlanet, context);
}
// Present blank form for adding a new waypoint
function addWaypoint(spawnName) {
	$("#waypointFormTitle").html('New Waypoint');
	$('#wpID').val('');
	if (spawnName == null) {
		$('#wpSpawn').val('');
	} else {
		$('#wpSpawn').val(spawnName);
	}
	$('#wpLocation').val('');
	$('#wpConcentration').val('');
	$('#wpPrice').val('');
	$('#wpCode').val('');
	$('#wpName').val('');
	$("#addInfo").html('');
	$('#sendWaypointData').text('Create');
	showWindow('#waypointDialog');
	return true;
}
// try to add waypoint
function postWaypoint() {
	if (true) {
		$('#busyImgAdd').css('display','block');
		$("#addInfo").html('');
		$.post(BASE_SCRIPT_URL + "postWaypoint.py", { wpID: $("#wpID").val(), galaxy: $("#galaxySel option:selected").val(), planet: $("#wpPlanetSel option:selected").val(), resName: $("#wpSpawn").val(), location: $("#wpLocation").val(), concentration: $("#wpConcentration").val(), price: $("#wpPrice").val(), wpName: $("#wpName").val(), shareLevel: $("#wpSharing").val() },
			function(data) {
				var result = $(data).find('resultText').eq(0).text();
				var newID = $(data).find("waypointID").eq(0).text();
				$("#addInfo").html(result);
				$('#busyImgAdd').css('display','none');
				//$("#mask, .window").hide();
				if (window.location.pathname.indexOf("waypointMaps") > -1) {
					refreshWaypoints();
				} else if (window.location.pathname.indexOf("resource") > -1) {
					findWaypoints("spawn");
				} else {
					findWaypoints("recent");
				}
			}, "xml");
	}
	return true;
}
function editWaypoint(id) {
	$.get(BASE_SCRIPT_URL + "getWaypoints.py", { wpID: id, galaxy: $("#galaxySel option:selected").val(), rid: new Date() },
		function(data) {
			var result = $(data).find('resultText').eq(0).text();
			if (result.substr(0,6) == "Error:") {
				alert(result);
			}
			if (result == "found") {
				var wps = $(data).find('waypoint');
				var wp = null;
				var wpID = null;
				var lat = null;
				var lon = null;
				var spawn = null;
				var owner = null;
				var conc = null;
				var title = null;
				var wpType = null;
				var price = null;
				var shareLevel = null;
				for (i=0;i<wps.length;i++) {
					// get data for this waypoint
					wp = wps.eq(i);
					wpID = $(wp).attr('id');
					lat = wp.find('lattitude').eq(0).text();
					lon = wp.find('longitude').eq(0).text();
					spawn = wp.find('spawn').eq(0).text();
					owner = wp.find('owner').eq(0).text();
					conc = wp.find('concentration').eq(0).text();
					title = wp.find('title').eq(0).text();
					wpType = wp.find('waypointType').eq(0).text();
					// owner only attributes
					price = wp.find('price').eq(0).text();
					shareLevel = wp.find('shareLevel').eq(0).text();

					// set form
					$("#waypointFormTitle").html('Edit Waypoint');
					$("#addInfo").html('');
					$("#wpID").val(wpID);
					$("#wpSpawn").val(spawn);
					$("#wpLocation").val(lat + ', ' + lon);
					$("#wpConcentration").val(conc);
					$("#wpPrice").val(price);
					$("#wpName").val(title);
					$("#wpSharing").val(shareLevel);
				}
			}
		}, "xml");
	$('#sendWaypointData').text('Update');
	showWindow('#waypointDialog');
	return true;
}
// Remove a waypoint
function deleteWaypoint(id) {
    var doit = false;
    doit = confirm("Do you really want to delete the waypoint?");

    if (doit) {
        $.get(BASE_SCRIPT_URL + "delWaypoint.py", {wpID: id, rid: new Date()}, function(data) {
	    if (data.indexOf("Error:")>-1) {
	        alert(data);
	    } else {
			if (data.indexOf("Waypoint removed")>-1) {
				$("#row_wp_"+id).empty();
	        	$("#row_wp_"+id).css("display","none");
			} else {
				refreshWaypoints();
				alert(data);
			}
	    }
	});
    }
	return true;
}

// Verify a waypoint
function verifyWaypoint(id) {
    var doit = false;
    doit = confirm("Do you want to verify the accuracy of this waypoint entry?");

    if (doit) {
        $.get(BASE_SCRIPT_URL + "postWaypoint.py", {wpID: id, forceOp: "verify", galaxy: $('#galaxySel option:selected').val(), rid: new Date()}, function(data) {
			var result = $(data).find('resultText').eq(0).text();
			refreshWaypoints();
	}, "xml");
    }
	return true;
}
//  Look up this users viewable waypoints for planet and paint them on map
function drawWaypoints(planet, ctx) {
	// clear existing data from waypoint table
	$('#waypointData').html('<tr class="tableHead"><th style="visibility:hidden;">Share</th><th width="100">Spawn</th><th width="20">Con.</th><th width="180">Resource Type</th><th width="320">Title</th><th width="40">X</th><th width="40">Y</th><th width="36">+</th><th width="100">Creator</th><th width="20">-</th><th style="display:none;">summary</th></tr>');
	// fetch planet waypoints
	$.get(BASE_SCRIPT_URL + "getWaypoints.py", { planetName: planet, galaxy: $("#galaxySel option:selected").val(), mine: $("#oMine:checked").val(), friends: $("#oFriends:checked").val(), pub: $("#oPublic:checked").val(), dshared: $("#oShared:checked").val(), minCon: $("#minConcentration").val(), uweeks: $("#weeksUnavailable").val(), rid: new Date() },
		function(data) {
			var result = $(data).find('resultText').eq(0).text();
			if (result.substr(0,6) == 'Error:') {
				alert(result);
			}
			if (result == 'found') {
				var showNoBuild = $("#oNoBuildZones:checked").val();
				var shareStr = '<td></td>';
				var wps = $(data).find('waypoint');
				var wp = null;
				var wpID = null;
				var lat = null;
				var lon = null;
				var spawn = null;
				var owner = null;
				var fetcher = null;
				var conc = null;
				var title = null;
				var wpType = null;
				var shareType = null;
				var resType = null;
				var resTypeID = null;
				var delCount = null;
				var verCount = null;
				var rowStr = '';
				for (i=0;i<wps.length;i++) {
					shareStr = '<td style="visibility:hidden;"></td>'
					delString = ''
					verString = ''
					// get data for this waypoint
					wp = wps.eq(i);
					wpID = $(wp).attr('id');
					lat = wp.find('lattitude').eq(0).text();
					lon = wp.find('longitude').eq(0).text();
					spawn = wp.find('spawn').eq(0).text();
					owner = wp.find('owner').eq(0).text();
					fetcher = wp.find('fetcher').eq(0).text();
					conc = wp.find('concentration').eq(0).text();
					title = wp.find('title').eq(0).text();
					wpType = wp.find('waypointType').eq(0).text();
					shareType = wp.find('shareLevel').eq(0).text();
					resType = wp.find('resType').eq(0).text();
					resTypeID = wp.find('resTypeID').eq(0).text();
					delCount = wp.find('delCount').eq(0).text();
					verCount = wp.find('verCount').eq(0).text();

					if (delCount != '0') {
						delString = '<span style="color:red;" title="' + delCount + ' people have marked this waypoint as no longer valid.">(' + delCount + ')</span>';
					}
					if (verCount != '0') {
						verString = '<span style="color:green;" title="' + verCount + ' people have verified this waypoint.">(' + verCount + ')</span>';
					}

					// draw on map
					if (ctx && (showNoBuild == "on" || wpType == 'u')) {
						drawWaypoint(parseInt(conc), (parseInt(lat) + 8192) / 20, (-parseInt(lon) + 8192) / 20, wpType, ctx, delCount);
					}
					// add data for user waypoints to data table last cell is data for tooltip
					commandInput = getWaypointCommandInput(planet, lat, lon, spawn, resType, conc);
					if (wpType == 'u') {
						if (owner == fetcher) {
							// Include edit links for owner
							rowStr = '<tr alt="' + wpID + '" class="statRow" id="row_wp_' + wpID + '"><td class="waypointRow">Copy</td><td><a href="' + BASE_SCRIPT_URL + 'resource.py/' + $("#galaxySel option:selected").val() + '/' + spawn + '" class="nameLink" title="View more information about this resource spawn">' + spawn + '</a> <a style="cursor:pointer;" onclick="editWaypoint(' + wpID + ');" title="Click to edit waypoint">[Edit]</a></td><td>' + conc + '%</td><td><a href="' + BASE_SCRIPT_URL + 'resourceType.py/' + resTypeID + '" class="nameLink">' + resType + '</a></td><td>' + title + '</td><td>' + lat + '</td><td>' + lon + '</td>';
							rowStr += '<td><img src="/images/checkGreen16.png" alt="check mark" title="Click to verify this waypoint" style="cursor:pointer;" onclick="verifyWaypoint(' + wpID + ');" />' + verString + '</td><td><a href="' + BASE_SCRIPT_URL + 'user.py/' + owner + '" class="nameLink" title="Go to user profile.">' + owner + '</a></td><td><a style="cursor:pointer;" onclick="deleteWaypoint(' + wpID + ');" title="Click to remove this waypoint">[X]</a>' + delString + '</td>';
							rowStr += '<td style="display:none;">&lt;span style="font-weight:bold;"&gt;' + spawn + '&lt;/span&gt; &lt;a style="cursor:pointer;" onclick="editWaypoint(' + wpID + ');"&gt;[Edit]&lt;/a&gt; &lt;div class="standOut"&gt;' + conc + '%&lt;/div&gt;' + lat + ', ' + lon + ' &lt;a style="cursor:pointer;" onclick="deleteWaypoint(' + wpID + ');"&gt;[X]&lt;/a&gt;' + commandInput + '</td></tr>';
						} else {
							rowStr = '<tr alt="' + wpID + '" class="statRow" id="row_wp_' + wpID + '"><td class="waypointRow">Copy</td><td><a href="' + BASE_SCRIPT_URL + 'resource.py/' + $("#galaxySel option:selected").val() + '/' + spawn + '" class="nameLink" title="View more information about this resource spawn">' + spawn + '</a></td><td>' + conc + '%</td><td><a href="' + BASE_SCRIPT_URL + 'resourceType.py/' + resTypeID + '" class="nameLink">' + resType + '</a></td><td>' + title + '</td><td>' + lat + '</td><td>' + lon + '</td><td><img src="/images/checkGreen16.png" alt="check mark" title="Click to verify this waypoint" style="cursor:pointer;" onclick="verifyWaypoint(' + wpID + ');" />' + verString + '</td>';
							rowStr += '<td><a href="' + BASE_SCRIPT_URL + 'user.py/' + owner + '" class="nameLink" title="Go to user profile.">' + owner + '</a></td><td><a style="cursor:pointer;" onclick="deleteWaypoint(' + wpID + ');" title="Click to remove this waypoint">[X]</a>' + delString + '</td><td style="display:none;">&lt;span style="font-weight:bold;"&gt;' + spawn + '&lt;/span&gt;  &lt;div class="standOut"&gt;' + conc + '%&lt;/div&gt;' + lat + ', ' + lon + ' &lt;a style="cursor:pointer;" onclick="deleteWaypoint(' + wpID + ');"&gt;[X]&lt;/a&gt;' + commandInput + '</td></tr>';
						}
						$('#waypointData').append(rowStr);
					}
				}
				addWaypointCopy();
			}
			$("#busyImgDrawWaypoints").hide();
		}, "xml");
	return true;
}
//  Paint a waypoint to the map
function drawWaypoint(conc, x, y, wpType, ctx, marks) {
	var wpColor = null;
	if (wpType != "u") {
		ctx.save();
		// mark non buildable radius around waypoint
		ctx.beginPath();
		ctx.arc(x, y, conc / 20, 0, Math.PI * 2, false);
		ctx.closePath();
		ctx.fillStyle = "rgba(255, 64, 64, 0.4)";
		ctx.fill();
		ctx.restore();
	} else {
		// regular waypoints are blue, red if marked unavailable
		if (marks == '0') {
			if (conc >= 50) {
				wpColor = Colors.ColorFromHSV(180,(conc-50)/50,.72);
			} else {
				wpColor = Colors.ColorFromHSV(180,conc/50,.62);
			}
		} else {
			wpColor = Colors.ColorFromHSV(10,conc/100,.72);
		}
		ctx.save();
		ctx.beginPath();
		ctx.moveTo(x, y);
		// draw stem
		ctx.lineTo(x+10, y-10);
		ctx.lineTo(x+12, y-10);
		ctx.lineTo(x+2, y);
		ctx.lineTo(x, y);
		// draw triangle
		ctx.moveTo(x+10, y-10);
		ctx.lineTo(x+30, y-10);
		ctx.lineTo(x+20, y-25);
		ctx.lineTo(x+10, y-10);
		ctx.closePath();

		ctx.strokeStyle = "#0000ff";
		ctx.stroke();
		ctx.fillStyle = wpColor.HexString();
		ctx.fill();
		ctx.restore();
	}

	return true;
}
//  Search for waypoints
function findWaypoints(displayType) {
	// clear existing data from waypoint table
	if (displayType == 'recent') {
		$('#findWaypointsList').html('<tr class="tableHead"><th>Spawn</th><th>Con.</th><th>Owner</th><th>Added</th><th><img src="/images/waypointMarker.png" alt="waypoint marker" title="stronger color associated with higher concentration" width="16" /></th><th style="display:none;">summary</th></tr>');
	} else if (displayType == 'spawn') {
		$('#findWaypointsList').html('<tr class="tableHead"><th>Added</th><th>Con.</th><th>Planet</th><th>X</th><th>Y</th><th style="display:none;">summary</th></tr>');
	} else {
		$('#findWaypointsList').html('<tr class="tableHead"><th>Spawn</th><th>Con.</th><th>Planet</th><th>X</th><th>Y</th><th style="display:none;">summary</th></tr>');
	}
	$('#busyImgSearch').css('display','block');
	// fetch planet waypoints
	$.get(BASE_SCRIPT_URL + "getWaypoints.py", { spawnName: $('#findSpawn').val(), galaxy: $("#galaxySel option:selected").val(), mine: 'on', friends: 'on', pub: 'on', dshared: 'on', sortType: displayType, rid: new Date() },
		function(data) {
			var result = $(data).find('resultText').eq(0).text();
			if (result.substr(0,6) == "Error:") {
				alert(result);
			}
			if (result == "found") {
				var wps = $(data).find('waypoint');
				var wp = null;
				var wpID = null;
				var lat = null;
				var lon = null;
				var spawn = null;
				var owner = null;
				var conc = null;
				var title = null;
				var wpType = null;
				var planet = null;
				var shareType = null;
				var added = null;
				var price = null;
				var wpColor = null;
				var resType = null;
				var commandInput = null;
				for (i=0;i<wps.length;i++) {
					// get data for this waypoint
					wp = wps.eq(i);
					wpID = $(wp).attr("id");
					lat = wp.find("lattitude").eq(0).text();
					lon = wp.find("longitude").eq(0).text();
					spawn = wp.find('spawn').eq(0).text();
					owner = wp.find('owner').eq(0).text();
					conc = wp.find('concentration').eq(0).text();
					title = wp.find('title').eq(0).text();
					wpType = wp.find('waypointType').eq(0).text();
					planet = wp.find('planet').eq(0).text();
					shareType = wp.find('shareLevel').eq(0).text();
					added = wp.find('added').eq(0).text();
					resType = wp.find('resType').eq(0).text();
					if (conc >= 50) {
						wpColor = Colors.ColorFromHSV(180,(conc-50)/50,.72);
					} else {
						wpColor = Colors.ColorFromHSV(180,conc/50,.62);
					}

					if (shareType == '256') {
						price = 'Public'
					} else if (shareType == '64') {
						price = 'Friends'
					} else {
						price = wp.find('price').eq(0).text() + 'c';
					}
					// add data for user waypoints to data table
					commandInput = getWaypointCommandInput(planet, lat, lon, spawn, resType, conc);
					if (wpType == 'u') {
						if (displayType == 'recent') {
							$('#findWaypointsList').append('<tr alt="' + wpID + '" class="statRow waypointRow" title="' + resType + ': ' + title + '"><td><a href="' + BASE_SCRIPT_URL + 'resource.py/' + $("#galaxySel option:selected").val() + '/' + spawn + '">' + spawn + '</a></td><td>' + conc + '%</td><td><a href="' + BASE_SCRIPT_URL + 'user.py/' + owner + '">' + owner + '</a></td><td>' + added + ' ago</td><td><div class="triangle1" style="border-color:transparent ' + wpColor.HexString() + ' transparent transparent;"></div></td><td>' + commandInput + '</td></tr>');
						} else if (displayType == 'spawn') {
							$('#findWaypointsList').append('<tr alt="' + wpID + '" class="statRow waypointRow"><td>' + added + ' ago</td><td>' + conc + '%</td><td>' + planet + '</td><td>' + lat + '</td><td>' + lon + '</td><td>' + commandInput + '</td></tr>');
						} else {
							$('#findWaypointsList').append('<tr alt="' + wpID + '" class="statRow waypointRow"><td><a href="' + BASE_SCRIPT_URL + 'resource.py/' + $("#galaxySel option:selected").val() + '/' + spawn + '">' + spawn + '</a></td><td>' + conc + '%</td><td>' + planet + '</td><td>' + lat + '</td><td>' + lon + '</td><td>' + commandInput + '</td></tr>');
						}
					}
				}
				addWaypointCopy();
			}
			$('#busyImgWaypointSearch').css('display','none');
		}, "xml");
	return true;
}

function getWaypointCommandInput(planet, lat, lon, spawn, resType, conc) {
	// prepare an input element with value of waypoint creation command for ingame which browser can copy to clipboard
	var waypointCommand = '/waypoint ' + planet.replace(' ', '').replace('YavinIV', 'yavin4') + ' ' + lat + ' ' + lon + ' ' + spawn + ' ' + resType + ' ' + conc;
	var commandInput = '<input type="text" value="' + waypointCommand + '"></input>';
	return commandInput;
}

function addWaypointCopy() {
	// Add click function to all waypoint rows for copying waypoint command to clipboard
	$('.waypointRow').click( function() {
		var copySource = $(this).find('input[type="text"]:first');
		copySource.select();
		document.execCommand('Copy');
		alert('Waypoint copied to clipboard.');
		this.focus()
	});
}



/*     Friend Functions    */

function addFriend(uid) {
	$.post(BASE_SCRIPT_URL + "changeFriend.py",{ op: "add", friend: uid },
		function(data) {
			if (data.substr(0,5) == "Error") {
				alert(data);
			} else {
				$("#friendStatus").fadeOut(300);
				$("#friendStatus").html(data);
				$("#friendStatus").fadeIn(300);
			}
		}, "html");
}
function removeFriend(uid) {
	$.post(BASE_SCRIPT_URL + "changeFriend.py",{ op: "remove", friend: uid },
		function(data) {
			if (data.substr(0,5) == "Error") {
				alert(data);
			} else {
				// if friend row exists update for profile page, otherwise we need to update for other individual page
				if ($("#frow_" + uid).length > 0) {
				    $("#frow_" + uid).fadeOut(300);
				} else {
					$("#friendStatus").html('<button type=button value="Add To Friends" class="ghButton" onclick="addFriend(\'' + uid + '\');">Add To Friends</button>');
				}
			}
		}, "html");
}

/*      Alert Filter Functions     */

// load existing saved alert filters
function loadAlerts(linkappend) {
	var maxRow = 0;
	// Fetch filter data
	$.post(BASE_SCRIPT_URL + "getFilters.py?" + linkappend, { galaxy: $("#galaxySel option:selected").val()},
		function(data) {
			$(data).find('filter').each (function() {
					fltOrder = $(this).find('fltOrder').eq(0).text();
					fltQuality = $(this).find('fltQuality').eq(0).text();
					if ( fltQuality != "0" && fltQuality != "None" ) {
						addFilterRow('addQualityAlertTable', fltOrder);
					} else {
						addFilterRow('addAlertTable', fltOrder);
					}
					if ($(this).find('fltType').eq(0).text() == "2") {
						$('#oGroup' + fltOrder).attr("checked","checked");
					}
					setTGlist(fltOrder);
					// Set a property with the value first incase it hasn't been populated with options yet
					$('#typeGroupSel' + fltOrder).attr("tag", $(this).find('fltValue').eq(0).text());
					$('#typeGroupSel' + fltOrder).val($(this).find('fltValue').eq(0).text());
					aTypes = $(this).find('alertTypes').eq(0).text();
					if (aTypes != "1" && aTypes != "3" && aTypes != "5" && aTypes != "7") {
						$('#oHome' + fltOrder).removeAttr("checked");
					} else {
            $('#oHome' + fltOrder).attr("checked","checked");
          }
					if (aTypes != "2" && aTypes != "3" && aTypes != "6" && aTypes != "7") {
						$('#oEmail' + fltOrder).removeAttr("checked");
					} else {
            $('#oEmail' + fltOrder).attr("checked","checked");
          }
          if (aTypes != "4" && aTypes != "5" && aTypes != "6" && aTypes != "7") {
            $('#oMobile' + fltOrder).removeAttr("checked");
          } else {
            $('#oMobile' + fltOrder).attr("checked","checked");
          }
					if ($(this).find('CRmin').eq(0).text() != "0") {
						$('#CR' + fltOrder).val($(this).find('CRmin').eq(0).text());
					}
					if ($(this).find('CDmin').eq(0).text() != "0") {
						$('#CD' + fltOrder).val($(this).find('CDmin').eq(0).text());
					}
					if ($(this).find('DRmin').eq(0).text() != "0") {
						$('#DR' + fltOrder).val($(this).find('DRmin').eq(0).text());
					}
					if ($(this).find('FLmin').eq(0).text() != "0") {
						$('#FL' + fltOrder).val($(this).find('FLmin').eq(0).text());
					}
					if ($(this).find('HRmin').eq(0).text() != "0") {
						$('#HR' + fltOrder).val($(this).find('HRmin').eq(0).text());
					}
					if ($(this).find('MAmin').eq(0).text() != "0") {
						$('#MA' + fltOrder).val($(this).find('MAmin').eq(0).text());
					}
					if ($(this).find('PEmin').eq(0).text() != "0") {
						$('#PE' + fltOrder).val($(this).find('PEmin').eq(0).text());
					}
					if ($(this).find('OQmin').eq(0).text() != "0") {
						$('#OQ' + fltOrder).val($(this).find('OQmin').eq(0).text());
					}
					if ($(this).find('SRmin').eq(0).text() != "0") {
						$('#SR' + fltOrder).val($(this).find('SRmin').eq(0).text());
					}
					if ($(this).find('UTmin').eq(0).text() != "0") {
						$('#UT' + fltOrder).val($(this).find('UTmin').eq(0).text());
					}
					if ($(this).find('ERmin').eq(0).text() != "0") {
						$('#ER' + fltOrder).val($(this).find('ERmin').eq(0).text());
					}
					if ( fltQuality != "0" && fltQuality != "None" ) {
						$('#minQuality' + fltOrder).val($(this).find('fltQuality').eq(0).text());
					}
					$('#fltGroup' + fltOrder).val($(this).find('fltGroup').eq(0).text());
					tmpRow = parseInt(fltOrder);
					if (tmpRow > maxRow) {
						maxRow = tmpRow;
					}
				});
			var result = $(data).find('resultText').eq(0).text();
			$("#sentMessage").html(result);
			$("#alertMask").css("display","none");
			$("#udBusyImg").css("display","none");
			$("#sendResponse").html($(data).find('fltCount').eq(0).text());
			addFilterRow("addQualityAlertTable", maxRow + 1);
			addFilterRow("addAlertTable", maxRow + 2);
			setTGlist(maxRow + 1);
			setTGlist(maxRow + 2);
		}, "xml");
	return;
}

// saves changes to user filters for alerts
function updateAlerts(linkappend) {
	fltStr = "";
	numRes = 0;
	if ($("#galaxySel option:selected").val() == 0) {
		alert("Select a galaxy first please.");
	} else {
		$("#resultInfo").html("");
		$("#udBusyImg").css("display","inline");
		$("#alertMask").css("display","block");
		orders = "";
		types = "";
		values = "";
		alerts = "";
		CRs = "";
		CDs = "";
		DRs = "";
		FLs = "";
		HRs = "";
		MAs = "";
		PEs = "";
		OQs = "";
		SRs = "";
		UTs = "";
		ERs = "";
		qualities = "";
		groups = "";
		errors = 0;
		// Compile comma separate list of each column value
		$(".filterRow").each (function() {
			fltType = "";
      x = $(this).attr("id").substr(6);
			fltValue = $("#typeGroupSel"+x+" option:selected").val();
			alertTypes = 0;
			qualityRow = 0;
			if (fltValue != null && fltValue != "none") {
				numRes += 1;
				if ( $("#minQuality"+x).val() != null && isNaN(parseInt($("#minQuality"+x).val())) ) {
					errors += 1;
				}
				if ($("#oType" + x).attr("checked") == "checked") {
					fltType = "1"
				} else {
					fltType = "2"
				}
				if ($("#oHome" + x).attr("checked") == "checked") {
					alertTypes += 1;
				}
				if ($("#oEmail" + x).attr("checked") == "checked") {
					alertTypes += 2;
				}
        if ($("#oMobile" + x).attr("checked") == "checked") {
					alertTypes += 4;
				}
				orders = orders + "," + x;
				types = types + "," + fltType;
				values = values + "," + fltValue;
				CRs = CRs + "," + $("#CR"+x).val();
				CDs = CDs + "," + $("#CD"+x).val();
				DRs = DRs + "," + $("#DR"+x).val();
				FLs = FLs + "," + $("#FL"+x).val();
				HRs = HRs + "," + $("#HR"+x).val();
				MAs = MAs + "," + $("#MA"+x).val();
				PEs = PEs + "," + $("#PE"+x).val();
				OQs = OQs + "," + $("#OQ"+x).val();
				SRs = SRs + "," + $("#SR"+x).val();
				UTs = UTs + "," + $("#UT"+x).val();
				ERs = ERs + "," + $("#ER"+x).val();
				qualities = qualities + "," + $("#minQuality"+x).val();
				alerts = alerts + "," + alertTypes;
        groups = groups + "," + $("#fltGroup"+x).val();
			}
		});
		// See if zero has been entered
		if (CRs.indexOf(",0") > -1 || CDs.indexOf(",0") > -1 || DRs.indexOf(",0") > -1 || FLs.indexOf(",0") > -1 || HRs.indexOf(",0") > -1
        || MAs.indexOf(",0") > -1 || PEs.indexOf(",0") > -1 || OQs.indexOf(",0") > -1 || SRs.indexOf(",0") > -1 || UTs.indexOf(",0") > -1
        || ERs.indexOf(",0") > -1) {
			alert("You have entered zero for one of the minimum stat values.  This will cause the stat to be ignored.  If you want to be alerted if the stat is of any value, enter 1 for the minimum value.");
		}
		if (errors > 0) {
			alert("You have selected a type for a Quality Based alert but not specified a minimum quality.  Please enter a valid minimum quality (1-1000) to continue.");
			$("#alertMask").css("display","none");
			$("#udBusyImg").css("display","none");
			return true;
		}
		var doit = false;
		if (!values.length > 0) {
			doit = confirm("This will delete all of your Alert filters, are you sure you want to do this?");
		}
		if (doit || values.length > 0) {
			// Trim extra comma
			orders = orders.substr(1);
			types = types.substr(1);
			values = values.substr(1);
			CRs = CRs.substr(1);
			CDs = CDs.substr(1);
			DRs = DRs.substr(1);
			FLs = FLs.substr(1);
			HRs = HRs.substr(1);
			MAs = MAs.substr(1);
			PEs = PEs.substr(1);
			OQs = OQs.substr(1);
			SRs = SRs.substr(1);
			UTs = UTs.substr(1);
			ERs = ERs.substr(1);
			qualities = qualities.substr(1);
			alerts = alerts.substr(1);
			groups = groups.substr(1);
			// Sync server with selections
			$.post(BASE_SCRIPT_URL + "updateFilters.py?" + linkappend, { galaxy: $("#galaxySel option:selected").val(), fltCount: numRes, fltOrders: orders, fltTypes: types, fltValues: values, CRmins: CRs, CDmins: CDs, DRmins: DRs, FLmins: FLs, HRmins: HRs, MAmins: MAs, PEmins: PEs, OQmins: OQs, SRmins: SRs, UTmins: UTs, ERmins: ERs, alertTypes: alerts, fltGroups: groups, qualityMins: qualities },
				function(data) {
					var result = $(data).find('resultText').eq(0).text();
					$("#sentMessage").html(result);
					$("#alertMask").css("display","none");
					$("#udBusyImg").css("display","none");
				}, "xml");
		}
		return false;
	}
}

// Update status of an alert usually to dismiss it
function updateAlertStatus(alertID, newStatus) {

    if (alertID) {
        $.post(BASE_SCRIPT_URL + "udAlert.py", {alert: alertID, status: newStatus}, function(data) {
	    if (data.indexOf("Error:")>-1) {
	        alert(data);
	    } else {
			$("#alert_"+data).fadeOut(300,function(){$("#alert_"+data).remove();});
	    }
	});
    }
}

function toggleAlertType(elm, itemID, favType) {
	alertType = 2;
	tmpClick = $(elm).attr("onclick");
	$(elm).removeAttr("onlick");
  $(elm).css("background-image","url(/images/ghWait16.gif)");

  if ($(elm).attr("tag") == "2") {
      // to browser alert
      alertType = 1;
      newBackground = "url(/images/browser16.png)";
      $(elm).attr("tag", "1");
      $(elm).attr("title", "home page");
  } else if ($(elm).attr("tag") == "4") {
      // to no alert
      alertType = 0;
      newBackground = "url(/images/none16.png)";
      $(elm).attr("tag", "0");
      $(elm).attr("title","None");
  } else if ($(elm).attr("tag") == "1") {
      // to mobile alert
      alertType = 4;
      newBackground = "url(/images/mobile16.png)";
      $(elm).attr("tag", "4");
      $(elm).attr("title", "mobile");
  } else {
      // to email alert
      newBackground = "url(/images/email16.png)";
      $(elm).attr("tag", "2");
      $(elm).attr("title","e-mail");
  }
	updateFavoriteAlert(itemID, alertType, favType, $("#galaxySel").val());
  $(elm).css("background-image", newBackground);
	$(elm).attr("onclick",tmpClick);
}

function loadDespawnAlerts(linkappend) {
	$("#despawnAlertsList").load(BASE_SCRIPT_URL + "getUserResources.py?" + linkappend,{
        galaxy: $("#galaxySel").val(),
        formatType: "alerts",
        favGroup: "any"},
        function() {
            $("#despawnBusyImg").css("display","none");
        });
    return false;
}

function addDespawnAlert(spawnName, alertTypes, linkappend) {
	if (spawnName) {
        $.post(BASE_SCRIPT_URL + "setFavorite.py?" + linkappend, {favType: 1, itemName: spawnName, galaxy: $("#galaxySel option:selected").val(), despawnAlert: 2}, function(data) {
	    if (data.indexOf("Error:")>-1) {
	        alert(data);
	    } else {
	        loadDespawnAlerts(linkappend);
	    }
	});
    }
}

function clearAlerts(alertType) {
	var doit = false;
	doit = confirm("Are you sure you want to clear all website alerts?");

	if (doit) {
        $.post(BASE_SCRIPT_URL + "udAlert.py", {alertType: alertType, status: 2}, function(data) {
	    if (data.indexOf("Error:")>-1) {
	        alert(data);
	    } else {
	        refreshAlerts();
	    }
	});
    }
}

/*      Feedback stuff         */

function loadFeedback() {
	var sortType = "rank"
	if ($("#oTime").attr("checked") == "checked") {
		sortType = "time";
	}
	$("#feedbackList").load(BASE_SCRIPT_URL + "getFeedback.py",{
		sort: sortType,
		perPage: "10"},
		function() {
			$("#feedbackBusyImg").css("display","none");
		});
	return false;
}

function voteFeedback(linkFrom, feedbackID, vote) {
	$.post(BASE_SCRIPT_URL + "postFeedback.py",{ itemID: feedbackID, voteValue: vote },
		function(data) {
			if (data.substr(0,5) == "Error") {
				alert(data);
			} else {
				if (vote > 0) {
					$(linkFrom).html($(linkFrom).html().replace('Grey','Green'));
				} else if (vote < 0) {
					$(linkFrom).html($(linkFrom).html().replace('Grey','Red'));
				} else {
					$(linkFrom).html($(linkFrom).html().replace('Red','Grey').replace('Green','Grey'));
				}
			}
		}, "html");
}

function moreFeedback(lastVal) {
	var sortType = "rank"
	if ($("#oTime").attr("checked") == "checked") {
		sortType = "time";
	}
	$.get("getFeedback.py",{sort:sortType, perPage:"10", lastItem: lastVal},
		function(data) {
		$("#moreButton").remove();
		$("#feedbackList").append(data);
	}, "html");
}

function postFeedback(feedbackID, feedbackText) {
	if (true) {
		$('#busyImgAdd').css('display','block');
		$("#addInfo").html('');
		$.post(BASE_SCRIPT_URL + "postFeedback.py", { itemID: feedbackID, suggestion: $("#feedbackText").val() },
			function(data) {
				var result = $(data).find('resultText').eq(0).text();
				var newID = $(data).find("feedbackID").eq(0).text();
				$("#addInfo").html(result);
				$('#busyImgAdd').css('display','none');
				$("#mask, .window").hide(3000);
				loadFeedback();
			}, "xml");
	}
	return true;
}

/*      Resource Type Stuff     */
// Present blank form for adding a new creature data
function addCreature(resourceType) {
	$("#creatureFormTitle").html('New Creature Data');
	$('#creatureName').val('');
  $('#creatureName').attr('disabled', false);
	$('#harvestYield').val('');
	$('#missionLevel').val('');
	$('#sendCreatureData').text('Add It');
  $('#addCreatureInfo').html('');
  $('#operation').val('');
	showWindow('#creatureDialog');
	return true;
}
// Present populated form for editing creature data
function editCreatureData(creatureName, harvestYield, missionLevel) {
	$("#creatureFormTitle").html('Edit Creature Data');
	$('#creatureName').val(creatureName);
  $('#creatureName').attr('disabled', true);
	$('#harvestYield').val(harvestYield);
  if (missionLevel == 'None') {
    missionLevel = '';
  }
	$('#missionLevel').val(missionLevel);
	$('#sendCreatureData').text('Update It');
  $('#addCreatureInfo').html('');
  $('#operation').val('edit');
	showWindow('#creatureDialog');
	return true;
}
// try to add creature data
function postCreature() {
	if (true) {
		$('#busyImgAdd').css('display','block');
		$("#addInfo").html('');
		$.post(BASE_SCRIPT_URL + "postCreature.py", { resourceType: $("#resourceType").val(), galaxy: $("#galaxySel option:selected").val(), creatureName: $("#creatureName").val(), harvestYield: $("#harvestYield").val(), missionLevel: $("#missionLevel").val(), forceOp: $("#operation").val() },
			function(data) {
				var result = $(data).find('resultText').eq(0).text();
				$("#addCreatureInfo").html(result);
				$('#busyImgAddCreature').css('display','none');
				//$("#mask, .window").hide();
				refreshCreatureData();
			}, "xml");
	}
	return true;
}
// Remove custom creature data
function removeCreatureResource(galaxy, resourceType, creature) {
  var doit = confirm("Do you really want to remove custom creature data for " + creature + "?");

  if (doit) {
      $.get(BASE_SCRIPT_URL + "delCreatureResource.py", {resType: resourceType, galaxy: galaxy, creatureName: creature, rid: new Date()}, function(data) {
      if (data.indexOf("Error:")>-1) {
        alert(data);
      } else {
        refreshCreatureData();
      }
    });
  }
}

/*      Other Shared Stuff     */

function showWindow(winId) {
    var maskHeight = $(document).height();
    var maskWidth = $(document).width();
    $("#mask").css({"width":maskWidth,"height":maskHeight});
    $("#mask").fadeIn(500);
    $("#mask").fadeTo("slow",0.8);
    var winH = $(window).height();
    var winW = $(window).width();
    $(winId).css("top", (winH/2-$(winId).height()/2) + $(window).scrollTop());
    $(winId).css("left", winW/2-$(winId).width()/2);
    $(winId).fadeIn(500);
}
function maskStats(typeSel, clearStats) {
    var statMask = "p00000000000";
	if (clearStats == null) clearStats = true;
	if (typeSel.selectedIndex > -1) {
    	statMask = typeSel.options[typeSel.selectedIndex].title;
	}
    if (typeSel.selectedIndex > 0) {
        $("#saveRes").removeAttr("disabled");
    } else {
        $("#saveRes").attr("disabled",true);
    }
    if (statMask.substr(1,1) == "0") {
        $("#CRheader").css("display", "none");
        $("#CRbox").css("display", "none");
    } else {
        $("#CRheader").css("display", "table-cell");
        $("#CRbox").css("display", "table-cell");
    }

    if (statMask.substr(2,1) == "0") {
        $("#CDheader").css("display", "none");
        $("#CDbox").css("display", "none");
    } else {
        $("#CDheader").css("display", "table-cell");
        $("#CDbox").css("display", "table-cell");
    }

    if (statMask.substr(3,1) == "0") {
        $("#DRheader").css("display", "none");
        $("#DRbox").css("display", "none");
    } else {
        $("#DRheader").css("display", "table-cell");
        $("#DRbox").css("display", "table-cell");
    }

    if (statMask.substr(4,1) == "0") {
        $("#FLheader").css("display", "none");
        $("#FLbox").css("display", "none");
    } else {
        $("#FLheader").css("display", "table-cell");
        $("#FLbox").css("display", "table-cell");
    }

    if (statMask.substr(5,1) == "0") {
        $("#HRheader").css("display", "none");
        $("#HRbox").css("display", "none");
    } else {
        $("#HRheader").css("display", "table-cell");
        $("#HRbox").css("display", "table-cell");
    }

    if (statMask.substr(6,1) == "0") {
        $("#MAheader").css("display", "none");
        $("#MAbox").css("display", "none");
    } else {
        $("#MAheader").css("display", "table-cell");
        $("#MAbox").css("display", "table-cell");
    }

    if (statMask.substr(7,1) == "0") {
        $("#PEheader").css("display", "none");
        $("#PEbox").css("display", "none");
    } else {
        $("#PEheader").css("display", "table-cell");
        $("#PEbox").css("display", "table-cell");
    }

    if (statMask.substr(8,1) == "0") {
        $("#OQheader").css("display", "none");
        $("#OQbox").css("display", "none");
    } else {
        $("#OQheader").css("display", "table-cell");
        $("#OQbox").css("display", "table-cell");
    }

    if (statMask.substr(9,1) == "0") {
        $("#SRheader").css("display", "none");
        $("#SRbox").css("display", "none");
    } else {
        $("#SRheader").css("display", "table-cell");
        $("#SRbox").css("display", "table-cell");
    }

    if (statMask.substr(10,1) == "0") {
        $("#UTheader").css("display", "none");
        $("#UTbox").css("display", "none");
    } else {
        $("#UTheader").css("display", "table-cell");
        $("#UTbox").css("display", "table-cell");
    }

    if (statMask.substr(11,1) == "0") {
        $("#ERheader").css("display", "none");
        $("#ERbox").css("display", "none");
    } else {
        $("#ERheader").css("display", "table-cell");
        $("#ERbox").css("display", "table-cell");
    }
	if (clearStats) {
		$("#CR0").val("");
		$("#CD0").val("");
		$("#DR0").val("");
		$("#FL0").val("");
		$("#HR0").val("");
		$("#MA0").val("");
		$("#PE0").val("");
		$("#OQ0").val("");
		$("#SR0").val("");
		$("#UT0").val("");
		$("#ER0").val("");
	}
}
function switchGalaxy(galaxy) {
	setCookie("galaxy", galaxy, 999);
	window.location.reload();
}
function toggleSection(aimg, id) {
	// hide or show resource list section and rotate arrow image
	var resContainer = $("#"+id);
	if (resContainer.css("display") == "none") {
		resContainer.css("display","block");
		$(aimg).css("-webkit-transform","rotate(0deg)");
		$(aimg).css("-moz-transform","rotate(0deg)");
		$(aimg).css("filter","progid:DXImageTransform.Microsoft.BasicImage(rotation=0)");
		setCookie("resListVis_" + id, "block", 365);
		// load resource data if section has not been loaded yet
		if (resContainer.html() == "") {
		    resContainer.load(BASE_SCRIPT_URL + "getResourceList.py",{
				galaxy: $("#galaxySel").val(),
			    unavailableDays: parseInt($("#weeksUnavailable").val())*7,
			    planetSel: $("#planetSel").val(),
            	resGroup: $("#resGroup").val(),
				resCategory: id.substr(5),
			    resType: $("#resType").val(),
			    sort: "type"},
			    function() {
				var resCount = $("#cont_" + id.substr(5)).find(".resourceBox").length;
				$("#title_" + id.substr(5)).append(" (" + resCount + ")");});
		}
	} else {
		$("#"+id).css("display","none");
		$(aimg).css("-webkit-transform","rotate(90deg)");
		$(aimg).css("-moz-transform","rotate(90deg)");
		$(aimg).css("filter","progid:DXImageTransform.Microsoft.BasicImage(rotation=2)");
		setCookie("resListVis_" + id, "none", 365);
	}
	return false;
}
// fills resource category group and sets up for next one
function populateResCategory() {
	var categoryID = resCategoryIDs[refreshPos];
	var contBox = $("#cont_" + categoryID);

	if (contBox.html() == "") {
		contBox.load(BASE_SCRIPT_URL + "getResourceList.py",{
			galaxy: $("#galaxySel").val(),
		    unavailableDays: parseInt($("#weeksUnavailable").val())*7,
		    planetSel: $("#planetSel").val(),
		    resGroup: $("#resGroup").val(),
		    resCategory: categoryID,
		    resType: $("#resType").val(),
                    favorite: $("#oFavorite:checked").val()},
			function(){
				var resCount = contBox.find(".resourceBox").length;
				$("#title_" + categoryID).append(" (" + resCount + ")");
			});
	}
	// set up next category for update
	refreshPos += 1;
	if (refreshPos < resCategoryIDs.length) {
		setTimeout("populateResCategory()", 500);
	}
}
// populates a resource category section on resource list page
function loadCategory(container, categoryID, categoryName) {
    var thisVis = getCookie('resListVis_cont_' + categoryID);
    if (thisVis == null || thisVis == '') thisVis = 'none';
	// print HTML for container
    container.append('<h2 class="categoryHead" style="margin-top:10px;" onclick="toggleSection($(\'#toggle_' + categoryID + '\'), \'cont_' + categoryID + '\');"><span id="title_' + categoryID + '">' + categoryName + '</span><img id="toggle_' + categoryID + '" src="/images/downArrowGrey16.png" title="Click to hide/show this section" class="control" style="float:right;position:relative;" /><span id="note_' + categoryID + '" class="statMax" style="float:right;position:relative;font-weight:normal;display:none;">Click to hide/show section.&nbsp;</span></h2><div id="cont_' + categoryID + '" style="display:' + thisVis + ';"></div>');
    var aimg = $('#toggle_' + categoryID);
	// load resource data if section was expanded according to cookie
	// otherwise it will get loaded later on the timer with populateResCategory
    if (thisVis == 'none') {
		aimg.css("-webkit-transform","rotate(90deg)");
		aimg.css("-moz-transform","rotate(90deg)");
		aimg.css("filter","progid:DXImageTransform.Microsoft.BasicImage(rotation=2)");
    } else {
		$('#cont_' + categoryID).html('<div id="busyImg_' + categoryID + '" style="text-align:center;" class="lds-ripple"><div></div><div></div></div>');
        $("#cont_" + categoryID).load(BASE_SCRIPT_URL + "getResourceList.py",{
			galaxy: $("#galaxySel").val(),
            unavailableDays: parseInt($("#weeksUnavailable").val())*7,
            planetSel: $("#planetSel").val(),
            resGroup: $("#resGroup").val(),
			resCategory: categoryID,
            resType: $("#resType").val(),
		favorite: $("#oFavorite:checked").val()},
			function(){
				var resCount = $("#cont_" + categoryID).find(".resourceBox").length;
				$("#title_" + categoryID).append(" (" + resCount + ")");
			});
    }
	return false;
}
function attachCategoryEvents() {
	$("h2.categoryHead").hover(function(){
		$(this).children("span.statMax").show("fast");
	},function(){
		$(this).children("span.statMax").hide("fast");
	});
}
function contactMessage() {
	alert('If you have a question, problem, or suggestion with the site, please send an email to galaxyharvester@gmail.com');
}
String.prototype.trim = function () {
  return this.replace(/^\s*/, "").replace(/\s*$/, "");
}
function switchImageInput() {
	// alternate image setting options for schematic page
	if ($("#useExisting").val() == "on") {
		$("#schemImage").fadeOut("1000");
		$("#copyFromSchem").fadeIn("1000");
	} else {
		$("#copyFromSchem").val("");
		$("#copyFromSchem").fadeOut("1000");
		$("#schemImage").fadeIn("1000");
	}
}
// Validation for email
function valEmail(email) {
  var infBox = document.getElementById('emailInf');
  if (email.value.length < 6 || email.value.indexOf('@') == -1) {
    infBox.style.visibility = 'visible';}
  else {
    infBox.style.visibility = 'hidden';}
}
// Validation for waypoint location entry
function valLocation(wpLoc) {
  var infBox = document.getElementById('locInf');
  if (isNaN(parseInt(wpLoc.value)) || wpLoc.value.indexOf(',') == -1) {
    infBox.style.visibility = 'visible';}
  else {
    infBox.style.visibility = 'hidden';}
}
function valVpass(passwd,vpasswd) {
  var pass1 = document.getElementById(passwd);
  var infBox = document.getElementById('vpassInf');
  if (pass1.value != vpasswd.value) {
    infBox.style.visibility = 'visible';}
  else {
    infBox.style.visibility = 'hidden';}
}
// Generic validation function for a minimum length
function valMinLength(elm, infElm, valLen) {
  if (elm.value.length < valLen) {
    infElm.style.visibility = 'visible';}
  else {
    infElm.style.visibility = 'hidden';}
}
// Generic validation function for an integer
function valInteger(elm, infElm) {
  if (isNaN(elm.value) || elm.value.indexOf('.') > -1) {
    infElm.style.visibility = 'visible';}
  else {
    infElm.style.visibility = 'hidden';}
}
// Generic validation function for a number
function valNumber(elm, infElm) {
  if (isNaN(elm.value)) {
    infElm.style.visibility = 'visible';}
  else {
    infElm.style.visibility = 'hidden';}
}
// Generic validation function minimum value
function valMinValue(elm, infElm, minVal) {
  if (elm.value < minVal) {
    infElm.style.visibility = 'visible';}
  else {
    infElm.style.visibility = 'hidden';}
}
function getCookie(cName, defaultValue) {
  if (document.cookie.length>0) {
	cStart = document.cookie.indexOf(cName + "=");
	if (cStart != -1) {
	    cStart = cStart + cName.length+1;
	    cEnd = document.cookie.indexOf(";",cStart);
	    if (cEnd == -1) cEnd = document.cookie.length;
	    return unescape(document.cookie.substring(cStart,cEnd));
	} else {
		return defaultValue;
	}
  }
  return defaultValue;
}
function setCookie(cName, value, expireDays) {
    var exdate = new Date();
    exdate.setDate(exdate.getDate()+expireDays);
    document.cookie=cName + "=" + escape(value)+((expireDays==null) ? "" : ";expires="+exdate.toUTCString()) + ";path=/";
    document.cookie=cName + "=" + escape(value)+((expireDays==null) ? "" : ";expires="+exdate.toUTCString()) + ";path=/resourceType.py";
}
/* Resource Stat Copy */
function addResourceCopy(resName) {
    var copySource = $("[data-resource='"+resName+"']").data("stats");
    var copyElement = document.createElement('input');
    copyElement.setAttribute('type', 'text');
    copyElement.setAttribute('value', copySource);
    copyElement = document.body.appendChild(copyElement);
    copyElement.select();
    document.execCommand('copy');
    document.body.removeChild(copyElement);
		alert(resName + ' resource data copied to clipboard.');
		this.focus()
}
