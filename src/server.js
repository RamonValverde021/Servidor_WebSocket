/*
// server.js
const WebSocket = require('ws');
const wss = new WebSocket.Server({ port: 8080 });

wss.on('connection', function connection(ws) {
  console.log('Novo cliente conectado');
  ws.on('message', function incoming(message) {
    console.log('Mensagem recebida:', message);
    // retransmitir para todos os clientes
    wss.clients.forEach(client => {
      if (client !== ws && client.readyState === WebSocket.OPEN) {
        client.send(message);
      }
    });
  });
});

console.log('Servidor WebSocket iniciado na porta 8080. Acesse em http://localhost:8080');
*/

const WebSocket = require('ws');
const PORT = 8080;
const wss = new WebSocket.Server({ port: PORT });

wss.on('connection', (ws, req) => {
    console.log('🔌 Cliente conectado:', req.socket.remoteAddress);

    ws.on('message', (message) => {
        console.log('📩 Mensagem recebida:', message.toString());

        // Resposta simples
        ws.send(`Servidor recebeu: ${message}`);
    });

    ws.on('close', () => {
        console.log('❌ Cliente desconectado');
    });
});

console.log(`✅ Servidor WebSocket iniciado na porta ${PORT}. Acesse em http://localhost:${PORT}`);
