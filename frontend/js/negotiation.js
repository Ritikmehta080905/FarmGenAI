const negotiationEvents = [

"Farmer lists Tomatoes 100kg",
"Buyer offers ₹18/kg",
"Farmer counters ₹19/kg",
"Buyer accepts deal",
"Transport assigned"

];

function startNegotiation(){

let log = document.getElementById("negotiationLog");

let i=0;

setInterval(()=>{

if(i<negotiationEvents.length){

let entry=document.createElement("div");

entry.className="log-entry";

entry.innerText=negotiationEvents[i];

log.appendChild(entry);

i++;

}

},2000);

}

startNegotiation();