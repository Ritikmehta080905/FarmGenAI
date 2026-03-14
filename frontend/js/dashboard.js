console.log("AgriNegotiator Dashboard Running");

renderAgents();
startNegotiation();
const ctx = document.getElementById("priceChart");

new Chart(ctx,{

type:"line",

data:{

labels:["Day1","Day2","Day3","Day4"],

datasets:[{

label:"Tomato Price",

data:[18,20,19,22]

}]

}

});