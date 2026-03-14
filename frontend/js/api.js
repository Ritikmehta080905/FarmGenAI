const API_BASE = "http://localhost:8000";

async function getAgents(){

const res = await fetch(`${API_BASE}/agents`);

return res.json();

}

async function getNegotiations(){

const res = await fetch(`${API_BASE}/negotiations`);

return res.json();

}

async function listCrop(data){

await fetch(`${API_BASE}/farmer/list`,{

method:"POST",

headers:{
"Content-Type":"application/json"
},

body:JSON.stringify(data)

});

}