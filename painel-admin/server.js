const express = require('express');
const { spawn } = require('child_process');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
const bodyParser = require('body-parser');
const path = require('path');
const sqlite3 = require('sqlite3').verbose();
const dayjs = require('dayjs');

// --- Configuração do Banco de Dados ---
const dbPath = path.resolve(__dirname, '..', 'auvo.db');
const db = new sqlite3.Database(dbPath, (err) => {
  if (err) {
    console.error('Erro ao conectar ao banco de dados SQLite:', err.message);
  } else {
    console.log('Conectado ao banco de dados SQLite.');
  }
});

const app = express();
const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: 'http://localhost:3000',
    methods: ['GET', 'POST'],
  },
});

app.use(cors());
app.use(bodyParser.json());

// --- Endpoints da API ---

// Endpoint para buscar os contratos
app.get('/api/contracts', (req, res) => {
  const allowed_contract_ids = [156750, 156751, 156752, 156753, 156754, 146168, 120805, 144297, 115503];
  const placeholders = allowed_contract_ids.map(() => '?').join(',');
  const query = `SELECT id, description as name FROM customer_groups WHERE id IN (${placeholders}) ORDER BY name`;

  db.all(query, allowed_contract_ids, (err, rows) => {
    if (err) {
      console.error("Erro ao buscar contratos:", err.message);
      res.status(500).json({ error: err.message });
      return;
    }
    res.json(rows);
  });
});

// Endpoint para gerar o relatório de faturamento
app.get('/api/faturamento', (req, res) => {
  try {
    console.log(`[${new Date().toISOString()}] /api/faturamento: Recebida requisição com query:`, req.query);
    const { group_id, start_date, end_date } = req.query;

    if (!group_id || !start_date || !end_date) {
      console.log(`[${new Date().toISOString()}] /api/faturamento: Parâmetros faltando.`);
      return res.status(400).json({ error: 'Parâmetros group_id, start_date e end_date são obrigatórios.' });
    }
    
    const end_date_inclusive = dayjs(end_date).endOf('day').format('YYYY-MM-DD HH:mm:ss');
    console.log(`[${new Date().toISOString()}] /api/faturamento: Buscando para o grupo ${group_id} no período de ${start_date} a ${end_date_inclusive}`);

    // A tabela 'customers' tem uma coluna 'groupsId' que parece ser um JSON array em string.
    // Usamos LIKE para encontrar os clientes que pertencem ao grupo.
    const getCustomerIdsQuery = `SELECT id FROM customers WHERE groupsId LIKE ?`;
    const likePattern = `%${group_id}%`;
    
    console.log(`[${new Date().toISOString()}] /api/faturamento: Buscando clientes com o padrão: ${likePattern}`);
    db.all(getCustomerIdsQuery, [likePattern], (err, customers) => {
      if (err) {
        console.error(`[${new Date().toISOString()}] /api/faturamento: Erro ao buscar clientes:`, err.message);
        return res.status(500).json({ error: 'Erro interno do servidor ao buscar clientes.' });
      }

      if (customers.length === 0) {
        console.log(`[${new Date().toISOString()}] /api/faturamento: Nenhum cliente encontrado para o grupo ${group_id}. Retornando vazio.`);
        return res.json([]);
      }

      const customerIds = customers.map(c => c.id);
      console.log(`[${new Date().toISOString()}] /api/faturamento: Encontrados ${customerIds.length} clientes. IDs: ${customerIds.join(', ')}`);
      
      const placeholders = customerIds.map(() => '?').join(',');
      const getTasksQuery = `
        SELECT
            t.idUserTo as user_id,
            u.name as user_name,
            t.taskStatus,
            t.orientation,
            c.description as school_name
        FROM tasks t
        JOIN users u ON t.idUserTo = u.userId
        LEFT JOIN customers c ON t.customerId = c.id
        WHERE t.customerId IN (${placeholders}) AND t.checkInDate BETWEEN ? AND ?
      `;
      
      const params = [...customerIds, start_date, end_date_inclusive];
      console.log(`[${new Date().toISOString()}] /api/faturamento: Executando consulta de tarefas.`);
      
      db.all(getTasksQuery, params, (err, tasks) => {
        if (err) {
          console.error(`[${new Date().toISOString()}] /api/faturamento: Erro ao buscar tarefas:`, err.message);
          return res.status(500).json({ error: 'Erro interno do servidor ao buscar tarefas.' });
        }

        console.log(`[${new Date().toISOString()}] /api/faturamento: Encontradas ${tasks.length} tarefas. Processando relatório.`);
        const report = {};
        tasks.forEach(task => {
          const userId = task.user_id;
          if (!report[userId]) {
            report[userId] = {
              user_name: task.user_name,
              tasks_completed: 0,
              tasks_total: 0,
              tasks: []
            };
          }

          const isCompleted = task.taskStatus === 5;
          report[userId].tasks_total += 1;
          if (isCompleted) {
            report[userId].tasks_completed += 1;
          }

          report[userId].tasks.push({
            orientation: task.orientation || 'N/A',
            school_name: task.school_name || 'N/A',
            status: isCompleted ? 'Finalizada' : 'Outro'
          });
        });
        
        const finalReport = Object.values(report).map(userData => {
          const total = userData.tasks_total;
          const completed = userData.tasks_completed;
          userData.productivity = total > 0 ? Math.round((completed / total) * 100) : 0;
          return userData;
        });

        console.log(`[${new Date().toISOString()}] /api/faturamento: Relatório final gerado com ${finalReport.length} entradas. Enviando resposta.`);
        res.json(finalReport.sort((a, b) => b.tasks_completed - a.tasks_completed));
      });
    });
  } catch (e) {
    console.error(`[${new Date().toISOString()}] /api/faturamento: Erro síncrono inesperado:`, e.message);
    res.status(500).json({ error: 'Erro inesperado no servidor.' });
  }
});


// Endpoint para iniciar o download de tarefas
app.post('/api/download-tasks', (req, res) => {
  const { startDate, endDate } = req.body;

  if (!startDate || !endDate) {
    return res.status(400).json({ message: 'As datas de início e fim são obrigatórias.' });
  }

  const scriptPath = path.join(__dirname, '..', 'downloads', 'download_all_user_tasks_v2.py');
  // Garante que estamos usando o python do ambiente virtual
  const pythonExecutable = path.join(__dirname, '..', '.venv', 'Scripts', 'python');
  
  const pythonProcess = spawn(pythonExecutable, [scriptPath, startDate, endDate]);

  console.log(`Iniciando download de tarefas de ${startDate} a ${endDate}...`);
  io.emit('progress', { message: 'Iniciando download...', percentage: 0 });

  pythonProcess.stdout.on('data', (data) => {
    const output = data.toString();
    try {
      const progress = JSON.parse(output);
      io.emit('progress', progress);
    } catch (error) {
      io.emit('progress', { message: output.trim() });
    }
  });

  pythonProcess.stderr.on('data', (data) => {
    const error = data.toString();
    console.error(`[Python Error]: ${error}`);
    io.emit('progress', { message: `Erro: ${error}`, error: true });
  });

  pythonProcess.on('close', (code) => {
    console.log(`Script Python finalizado com código ${code}`);
    if (code === 0) {
      io.emit('progress', { message: 'Download concluído com sucesso!', percentage: 100 });
    } else {
      io.emit('progress', { message: 'Ocorreu um erro durante o download.', error: true });
    }
  });

  res.status(202).json({ message: 'Processo de download iniciado.' });
});

// Endpoint para obter o resumo do contrato (total de equipamentos e os que não tiveram serviço)
app.get('/api/contract-summary', (req, res) => {
  const { group_id, start_date, end_date } = req.query;

  if (!group_id || !start_date || !end_date) {
    return res.status(400).json({ error: 'Parâmetros group_id, start_date e end_date são obrigatórios.' });
  }

  const likePattern = `%${group_id}%`;
  const end_date_inclusive = dayjs(end_date).endOf('day').format('YYYY-MM-DD HH:mm:ss');

  // 1. Buscar IDs dos clientes (escolas) no contrato usando LIKE, que é o método que funciona
  const getCustomerIdsQuery = `SELECT id FROM customers WHERE groupsId LIKE ?`;
  db.all(getCustomerIdsQuery, [likePattern], (err, customers) => {
    if (err) {
      console.error('Erro ao buscar clientes do grupo:', err);
      return res.status(500).json({ error: 'Erro ao buscar clientes do grupo.', details: err.message });
    }
    const customerIds = customers.map(c => c.id);
    if (customerIds.length === 0) {
      return res.json({ totalEquipments: 0, equipmentsWithoutService: [] });
    }

    const placeholders = customerIds.map(() => '?').join(',');

    // 2. Buscar todos os equipamentos ATIVOS para esses clientes
    const allEquipmentsQuery = `
      SELECT 
        e.id, 
        e.name as equipment_name, 
        e.identifier as equipment_identifier,
        c.id as customer_id,
        c.groupsId as group_id,
        c.description as customer_description
      FROM equipments e
      JOIN customers c ON e.associatedCustomerId = c.id
      WHERE e.associatedCustomerId IN (${placeholders})
      AND e.active = 1
      ORDER BY c.description, e.name
    `;
    db.all(allEquipmentsQuery, customerIds, (err, allEquipments) => {
      if (err) {
        console.error('Erro ao buscar equipamentos por cliente:', err);
        return res.status(500).json({ error: "Erro ao verificar equipamentos.", details: err.message });
      }

      // Combinar equipment_name e equipment_identifier e formatar o nome da escola
      const formattedEquipments = allEquipments.map(equip => {
        // Combinar nome e identificador do equipamento
        const combinedName = equip.equipment_identifier ? 
          `${equip.equipment_name} ${equip.equipment_identifier}` : 
          equip.equipment_name;
          
        return {
          ...equip,
          // Usar o nome combinado
          name: combinedName,
          // Formata o nome da escola no formato correto
          school_name: `${equip.group_id} - SEDUC UME ${equip.customer_description}`
        };
      });

      const totalEquipments = formattedEquipments.length;
      
      if (totalEquipments === 0) {
        return res.json({ totalEquipments: 0, equipmentsWithoutService: [] });
      }

      // 3. Buscar tarefas de preventiva para os CLIENTES no período e os equipamentos associados
      const tasksQuery = `
        SELECT equipmentsId
        FROM tasks
        WHERE customerId IN (${placeholders})
        AND (LOWER(orientation) LIKE '%preventiva mensal%' OR LOWER(orientation) LIKE '%pmoc%')
        AND checkInDate BETWEEN ? AND ?
      `;
      
      const params = [...customerIds, start_date, end_date_inclusive];

      db.all(tasksQuery, params, (err, tasks) => {
        if (err) {
          console.error('Erro ao buscar tarefas por cliente:', err);
          return res.status(500).json({ error: "Erro ao verificar tarefas.", details: err.message });
        }

        // 4. Processar tarefas para encontrar IDs de equipamentos com serviço
        const servicedEquipmentIds = new Set();
        tasks.forEach(task => {
          if (task.equipmentsId) {
            try {
              // Converte a string JSON para um array de IDs
              const equipmentIds = JSON.parse(task.equipmentsId);
              if (Array.isArray(equipmentIds)) {
                // Adiciona cada ID ao conjunto de equipamentos com serviço
                equipmentIds.forEach(id => servicedEquipmentIds.add(id));
              }
            } catch (err) {
              console.error('Erro ao processar equipmentsId:', err);
            }
          }
        });

        // 5. Filtrar equipamentos com e sem serviço
        const equipmentsWithService = [];
        const equipmentsWithoutService = [];
        
        // Agrupar equipamentos por escola
        const schoolMap = new Map();
        
        formattedEquipments.forEach(equipment => {
          const hasService = servicedEquipmentIds.has(equipment.id);
          
          // Adicionar ao array apropriado
          if (hasService) {
            equipmentsWithService.push(equipment);
          } else {
            equipmentsWithoutService.push(equipment);
          }
          
          // Agrupar por escola
          const schoolName = equipment.school_name;
          if (!schoolMap.has(schoolName)) {
            schoolMap.set(schoolName, {
              name: schoolName,
              with_service: [],
              without_service: []
            });
          }
          
          const schoolData = schoolMap.get(schoolName);
          if (hasService) {
            schoolData.with_service.push(equipment);
          } else {
            schoolData.without_service.push(equipment);
          }
        });
        
        // Converter o Map em um array para enviar como JSON
        const schoolsGrouped = Array.from(schoolMap.values());
        
        res.json({
          total_equipments: totalEquipments,
          equipments_with_service: equipmentsWithService,
          equipments_without_service: equipmentsWithoutService,
          schools_grouped: schoolsGrouped
        });
      });
    });
  });
});

// Endpoint para gerar relatório de faturamento por colaborador
app.get('/api/faturamento', (req, res) => {
  const { group_id, start_date, end_date } = req.query;
  
  if (!group_id || !start_date || !end_date) {
    return res.status(400).json({ error: "Parâmetros group_id, start_date e end_date são obrigatórios." });
  }

  // 1. Buscar os clientes associados ao contrato
  const customerQuery = `
    SELECT id FROM customers 
    WHERE groupsId = ? 
    ORDER BY description
  `;

  db.all(customerQuery, [group_id], (err, customers) => {
    if (err) {
      console.error("Erro ao buscar clientes:", err.message);
      return res.status(500).json({ error: "Erro ao buscar clientes.", details: err.message });
    }

    if (customers.length === 0) {
      return res.status(404).json({ error: "Nenhum cliente encontrado para este contrato." });
    }

    const customerIds = customers.map(c => c.id);
    const placeholders = customerIds.map(() => '?').join(',');

    // 2. Buscar tarefas concluídas por colaborador
    const tasksQuery = `
      SELECT 
        t.id, 
        t.orientation, 
        t.status, 
        t.equipmentsId,
        t.idUserFrom, 
        t.userFromName,
        c.id as customer_id,
        c.description as customer_description,
        c.groupsId as group_id
      FROM tasks t
      JOIN customers c ON t.customerId = c.id
      WHERE t.customerId IN (${placeholders})
      AND t.checkInDate BETWEEN ? AND ?
      ORDER BY t.userFromName, c.description
    `;

    db.all(tasksQuery, [...customerIds, start_date, end_date], (err, tasks) => {
      if (err) {
        console.error("Erro ao buscar tarefas:", err.message);
        return res.status(500).json({ error: "Erro ao buscar tarefas.", details: err.message });
      }

      // 3. Processar tarefas por colaborador
      const userMap = new Map();
      
      tasks.forEach(task => {
        const userId = task.idUserFrom;
        const userName = task.userFromName;
        
        if (!userMap.has(userId)) {
          userMap.set(userId, {
            user_id: userId,
            user_name: userName,
            tasks_completed: 0,
            tasks_total: 0,
            tasks: [],
            schools: new Map()
          });
        }
        
        const userData = userMap.get(userId);
        userData.tasks_total++;
        
        if (task.status === 'Concluída') {
          userData.tasks_completed++;
        }
        
        // Processar equipamentos da tarefa
        let equipmentIds = [];
        if (task.equipmentsId) {
          try {
            equipmentIds = JSON.parse(task.equipmentsId);
          } catch (e) {
            console.error('Erro ao processar equipmentsId:', e);
          }
        }
        
        // Formatar nome da escola sem os IDs dos equipamentos no início
        const schoolName = `${task.group_id} - SEDUC UME ${task.customer_description}`;
        
        // Adicionar tarefa aos dados do usuário
        userData.tasks.push({
          id: task.id,
          orientation: task.orientation,
          status: task.status,
          school_name: schoolName,
          equipment_ids: equipmentIds
        });
        
        // Agrupar por escola
        if (!userData.schools.has(schoolName)) {
          userData.schools.set(schoolName, {
            name: schoolName,
            equipment_count: 0,
            tasks: []
          });
        }
        
        const schoolData = userData.schools.get(schoolName);
        schoolData.tasks.push(task.id);
        schoolData.equipment_count += equipmentIds.length;
      });
      
      // Calcular produtividade e formatar dados finais
      const result = Array.from(userMap.values()).map(user => {
        // Converter escolas de Map para Array
        const schools = Array.from(user.schools.values()).map(school => ({
          name: school.name, // Nome da escola sem os IDs dos equipamentos
          equipment_count: school.equipment_count,
          tasks: school.tasks
        }));
        
        return {
          user_id: user.user_id,
          user_name: user.user_name,
          tasks_completed: user.tasks_completed,
          tasks_total: user.tasks_total,
          productivity: user.tasks_total > 0 ? Math.round((user.tasks_completed / user.tasks_total) * 100) : 0,
          tasks: user.tasks,
          schools: schools
        };
      });
      
      res.json(result);
    });
  });
});

const PORT = process.env.PORT || 3001;
server.listen(PORT, () => {
  console.log(`Servidor Node.js unificado rodando na porta ${PORT}`);
});
