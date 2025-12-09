const ws = new WebSocket("ws://localhost:8080");

ws.onopen = () => ws.send("Olá servidor!");
ws.onmessage = (e) => console.log(e.data);
ws.onclose = () => console.log("Conexão fechada");

function sendMessage() {
    const message = document.getElementById("message").value;
    ws.send(message);
}
