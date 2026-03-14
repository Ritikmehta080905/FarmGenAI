document.getElementById("cropForm")
.addEventListener("submit",(e)=>{

e.preventDefault();

let crop=document.getElementById("crop").value;
let qty=document.getElementById("qty").value;
let price=document.getElementById("price").value;

console.log(crop,qty,price);

alert("Produce listed successfully!");

});