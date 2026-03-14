function startSimulation(){

let output=document.getElementById("simulationOutput");

output.innerHTML="Running supply chain simulation...";

setTimeout(function(){

output.innerHTML="Simulation complete: Deal executed.";

},3000);

}