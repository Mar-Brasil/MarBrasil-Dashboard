import express from 'express';
import http from 'http';
import { Server } from 'socket.io';
import cors from 'cors';
import bodyParser from 'body-parser';
import { getUserNameById } from './db.js';

const app = express();
const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: '*',
    methods: ['GET', 'POST']
  }
});

app.use(cors());
app.use(bodyParser.json());

// Função utilitária para calcular tempo de execução (em minutos)
function calcularTempoExecucao(checkInDate, checkOutDate) {
  if (!checkInDate || !checkOutDate) return null;
  const start = new Date(checkInDate);
  const end = new Date(checkOutDate);
  const diffMs = end - start;
  if (isNaN(diffMs) || diffMs < 0) return null;
  return Math.round(diffMs / 60000); // minutos
}

// Webhook endpoint para Auvo
app.post('/webhook/auvo', async (req, res) => {
  const payload = req.body;
  if (
    payload?.result?.Entities &&
    Array.isArray(payload.result.Entities)
  ) {
    // Enriquecer cada tarefa
    const enrichedEntities = await Promise.all(
      payload.result.Entities.map(async (task) => {
        const nomeUsuario = await getUserNameById(task.idUserFrom);
        const tempoExecucao = calcularTempoExecucao(task.checkInDate, task.checkOutDate);
        return {
          ...task,
          nomeUsuario: nomeUsuario || task.idUserFrom,
          tempoExecucao, // minutos
        };
      })
    );
    const enrichedPayload = {
      ...payload,
      result: {
        ...payload.result,
        Entities: enrichedEntities,
      },
    };
    io.emit('auvo-task-event', enrichedPayload);
  } else {
    io.emit('auvo-task-event', payload);
  }
  res.status(200).json({ received: true });
});

// Teste básico para saber se o backend está rodando
app.get('/', (req, res) => {
  res.send('Painel Backend rodando!');
});

const PORT = process.env.PORT || 4000;
server.listen(PORT, () => {
  console.log(`Backend rodando na porta ${PORT}`);
});
