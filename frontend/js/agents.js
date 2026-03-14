const agents = [

{
name:"Farmer Agent",
img:"assets/farmer.png",
role:"Crop Producer"
},

{
name:"Buyer Agent",
img:"assets/buyer.png",
role:"Market Buyer"
},

{
name:"Warehouse",
img:"assets/warehouse.png",
role:"Storage Facility"
},

{
name:"Transporter",
img:"assets/transport.png",
role:"Logistics"
},

{
name:"Processor",
img:"assets/processor.png",
role:"Food Processing"
}

];

function renderAgents(){

const container = document.getElementById("agentContainer");

container.innerHTML="";

agents.forEach(agent=>{

const card = document.createElement("div");

card.className="agent-card-3d";

card.innerHTML=`

<img src="${agent.img}" class="agent-img">

<h3>${agent.name}</h3>

<p>${agent.role}</p>

`;

container.appendChild(card);

});

}

renderAgents();