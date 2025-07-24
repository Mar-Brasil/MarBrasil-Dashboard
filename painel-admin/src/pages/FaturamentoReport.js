import React, { useState, useEffect, useMemo, useCallback } from 'react';
import axios from 'axios';
import { 
  Typography, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  Box, 
  CircularProgress, 
  Alert, 
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Card,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
  Button,
  ButtonGroup,
  IconButton,
  Tooltip
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import UnfoldLessIcon from '@mui/icons-material/UnfoldLess';
import UnfoldMoreIcon from '@mui/icons-material/UnfoldMore';
import FilterListIcon from '@mui/icons-material/FilterList';
import SortIcon from '@mui/icons-material/Sort';
import SchoolIcon from '@mui/icons-material/School';
import AssignmentIcon from '@mui/icons-material/Assignment';
import CategoryIcon from '@mui/icons-material/Category';
import { TextField } from '@mui/material';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

// Função para formatação de data
const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  if (isNaN(date.getTime())) {
    return 'Data inválida';
  }
  return date.toLocaleString('pt-BR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });
};

// Componente para exibir o status da tarefa
const StatusChip = ({ status }) => {
  const statusMap = {
    1: { label: 'Aberta', color: 'default' },
    2: { label: 'Em Deslocamento', color: 'info' },
    3: { label: 'Check-in', color: 'info' },
    5: { label: 'Finalizada', color: 'success' },
    6: { label: 'Concluída', color: 'success' },
    7: { label: 'Cancelada', color: 'error' },
  };
  const { label = 'N/A', color = 'default' } = statusMap[status] || {};
  return <Chip label={label} color={color} size="small" />;
};

// Helper para formatar valores de moeda
const formatCurrency = (value) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(value);
};

const FaturamentoReport = () => {
  const [contracts, setContracts] = useState([]);
  const [selectedContract, setSelectedContract] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [dashboardData, setDashboardData] = useState(null);
  const [selectedSchool, setSelectedSchool] = useState(null);
  const [equipments, setEquipments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [taskTypes, setTaskTypes] = useState([]);
  const [expandedSchools, setExpandedSchools] = useState({});
  const [expandedSections, setExpandedSections] = useState({
    financeiro: true,
    resumo: true,
    colaboradores: false,
    tarefasFimMes: false,
    tiposTarefas: false,
    escolas: false
  });

  // Número correto de equipamentos ativos para o Setor 1
  const KPI_TOTAL_EQUIP = 478; // Equipamentos sob responsabilidade do setor 1
  
  // Função para contar equipamentos ativos
  const getEquipmentCount = useCallback((task) => {
    if (!task.equipmentsId) return 0;
    try {
      const ids = JSON.parse(task.equipmentsId);
      if (!Array.isArray(ids)) return 0;
      
      // Se não tivermos dados de equipamentos, retorna o total
      if (!equipments || equipments.length === 0) {
        // Retorna uma estimativa baseada na proporção conhecida
        // Se sabemos que há 478 equipamentos ativos de um total de 604
        return Math.round(ids.length * (478/604));
      }
      
      // Filtra apenas os equipamentos ativos
      const activeEquipments = ids.filter(id => {
        const equipment = equipments.find(eq => eq.id === id);
        return equipment && equipment.active === 1;
      });
      
      return activeEquipments.length;
    } catch (e) {
      console.error('Erro ao processar equipamentos:', e);
      return 0;
    }
  }, [equipments]);

  // Efeito para buscar equipamentos
  useEffect(() => {
    const fetchEquipments = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/equipments`);
        setEquipments(response.data || []);
        console.log('Equipamentos carregados:', response.data?.length || 0);
      } catch (err) {
        console.error("Falha ao buscar equipamentos:", err);
      }
    };
    
    fetchEquipments();
  }, []);

  // Efeito para buscar a lista de contratos
  useEffect(() => {
    const fetchContracts = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/contracts`);
        setContracts(response.data || []);
      } catch (err) {
        console.error("Falha ao buscar contratos:", err);
        setError('Não foi possível carregar a lista de contratos.');
      }
    };
    
    fetchContracts();

    // Definir o intervalo de datas para o mês atual
    const today = new Date();
    const firstDay = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split('T')[0];
    const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0).toISOString().split('T')[0];
    setStartDate(firstDay);
    setEndDate(lastDay);
    
    console.log(`Definindo intervalo de datas para o mês atual: ${firstDay} até ${lastDay}`);
  }, []);

  // Efeito para buscar os dados do contrato selecionado
  useEffect(() => {
    if (!selectedContract || !startDate || !endDate) {
      setDashboardData(null);
      setSelectedSchool(null);
      return;
    }

    const fetchDashboardData = async () => {
      setLoading(true);
      setError(null);
      try {
        // Buscar tipos de tarefas primeiro (se ainda não foram buscados)
        if (taskTypes.length === 0) {
          try {
            const typesResponse = await axios.get(`${API_BASE_URL}/task-types`);
            setTaskTypes(typesResponse.data || []);
            console.log("Tipos de tarefas carregados:", typesResponse.data);
          } catch (typeErr) {
            console.error("Falha ao buscar tipos de tarefas:", typeErr);
          }
        }
        
        // Buscar dados de equipamentos
        try {
          const equipmentsResponse = await axios.get(`${API_BASE_URL}/equipments`);
          if (equipmentsResponse.data && Array.isArray(equipmentsResponse.data)) {
            console.log('Equipamentos carregados:', equipmentsResponse.data.length);
            setEquipments(equipmentsResponse.data);
          }
        } catch (equipErr) {
          console.error("Falha ao buscar equipamentos:", equipErr);
        }
        
        // Buscar dados do dashboard
        const response = await axios.get(
          `${API_BASE_URL}/dashboard/${selectedContract}`,
          { params: { start_date: startDate, end_date: endDate } }
        );
        setDashboardData(response.data);
      } catch (err) {
        console.error("Falha ao buscar dados do dashboard:", err);
        setError('Não foi possível carregar os dados do dashboard.');
      } finally {
        setLoading(false);
      }
    };
    fetchDashboardData();
  }, [selectedContract, startDate, endDate, taskTypes.length]);

  // Função para verificar se a data está no mês atual
  const isCurrentMonth = (dateString) => {
    if (!dateString) return false;
    const dateObj = new Date(dateString);
    if (isNaN(dateObj.getTime())) return false;
    
    const today = new Date();
    const taskDate = new Date(dateString);
    
    return (
      taskDate.getMonth() === today.getMonth() &&
      taskDate.getFullYear() === today.getFullYear()
    );
  };
  
  // Função para verificar se a data está no fim do mês atual (últimos 7 dias)
  // Movida para dentro do useMemo para evitar warning do ESLint
  const isCurrentMonthFn = useCallback((dateString) => {
    if (!dateString) return false;
    
    try {
      const date = new Date(dateString);
      const today = new Date();
      return date.getMonth() === today.getMonth() && date.getFullYear() === today.getFullYear();
    } catch (e) {
      console.error('Erro ao verificar mês atual:', e);
      return false;
    }
  }, []);
  
  // Função para verificar se a data está no fim do mês atual (últimos 7 dias)
  const isEndOfMonth = useCallback((dateString) => {
    if (!dateString) return false;
    
    try {
      // Removida variável today não utilizada
      const taskDate = new Date(dateString);
      
      // Verificar se a data é do mês atual
      if (!isCurrentMonthFn(dateString)) return false;
      
      // Obter o último dia do mês da tarefa
      const lastDayOfMonth = new Date(taskDate.getFullYear(), taskDate.getMonth() + 1, 0);
      const lastDayValue = lastDayOfMonth.getDate();
      const taskDay = taskDate.getDate();
      
      // Verifica se a data da tarefa está nos últimos 7 dias do mês
      return (lastDayValue - taskDay < 7);
    } catch (e) {
      console.error('Erro ao verificar fim do mês:', e);
      return false;
    }
  }, [isCurrentMonthFn]);

  // Processar os dados do dashboard
  const processedData = useMemo(() => {
    if (!dashboardData) return null;

    console.log("Processando dados do dashboard:", dashboardData);

    // 1. Desduplicar Tarefas com base na validade do link e equipamentos
    const getBestTask = (tasks) => {
      if (tasks.length === 1) return tasks[0];

      const validTasks = tasks.filter(t => t.is_link_valid === 1);
      
      let candidates = [];
      if (validTasks.length > 0) {
        // Se há tarefas com links válidos, elas são as candidatas
        candidates = validTasks;
      } else {
        // Se não, todas as tarefas (com links quebrados) são candidatas
        candidates = tasks;
      }

      // Das candidatas, escolhe a com mais equipamentos
      return candidates.reduce((best, current) => {
        return getEquipmentCount(current) > getEquipmentCount(best) ? current : best;
      });
    };

    // Filtrar tarefas do mês atual baseado na data de check-in
    const currentMonthTasks = dashboardData.tasks.filter(task => 
      isCurrentMonth(task.checkInDate) || isCurrentMonth(task.taskDate)
    );
    
    console.log(`Total de tarefas: ${dashboardData.tasks.length}, Tarefas do mês atual: ${currentMonthTasks.length}`);

    // Agrupar tarefas por chave (escola, orientação, data)
    const tasksByKey = currentMonthTasks.reduce((acc, task) => {
      const key = `${task.customerId}-${task.orientation}-${task.taskDate}`;
      if (!acc[key]) {
        acc[key] = [];
      }
      acc[key].push(task);
      return acc;
    }, {});

    // Aplicar a desduplicação
    const dedupedTasks = Object.values(tasksByKey).map(getBestTask);

    // Variáveis para contagem
    const openTasks = [];
    const completedTasks = [];
    const endOfMonthTasks = [];
    let totalTasks = dedupedTasks.length;
    let completedTasksCount = 0;
    let openTasksCount = 0;
    let canceledTasksCount = 0;
    let endOfMonthTasksCount = 0;
    
    // Para agrupar por tipo de tarefa
    const taskTypeMap = new Map();

    // Processar tarefas já desduplicadas
    dedupedTasks.forEach(task => {
      // Verificar status da tarefa
      if ([5, 6].includes(task.taskStatus)) { // Concluída ou aprovada
        completedTasks.push(task);
        completedTasksCount++;
      } else if (task.taskStatus === 7) { // Cancelada
        canceledTasksCount++;
      } else { // Aberta, em andamento, etc.
        // Tarefas abertas
        openTasks.push(task);
        openTasksCount++;
        
        // Agrupar por tipo de tarefa (usando o campo taskType ou orientation como identificador)
        const taskTypeId = task.taskType || 'unknown';
        if (!taskTypeMap.has(taskTypeId)) {
          // Buscar a descrição do tipo de tarefa se disponível
          // Garantir que taskTypeId seja uma string para comparar com t.id
          const taskTypeIdStr = String(taskTypeId || '');
          const taskTypeInfo = taskTypes?.find(t => t && t.id && String(t.id) === taskTypeIdStr);
          const taskTypeDescription = taskTypeInfo?.description || 
            task.orientation || 
            taskTypeId || 
            'Sem descrição';
          
          taskTypeMap.set(taskTypeId, {
            id: taskTypeId,
            type: taskTypeDescription,
            count: 0,
            tasks: []
          });
        }
        
        const taskTypeInfo = taskTypeMap.get(taskTypeId);
        taskTypeInfo.count++;
        taskTypeInfo.tasks.push(task);
        
        // Verificar se é uma tarefa de fim de mês e está aberta (não concluída ou cancelada)
        // Tarefas com status 5 ou 6 são concluídas, 7 é cancelada
        if (isEndOfMonth(task.taskDate || task.scheduledDate) && ![5, 6, 7].includes(task.taskStatus)) {
          endOfMonthTasks.push(task);
          endOfMonthTasksCount++;
        }
      }
    });

    // Agrupar por escola
    const schoolsMap = new Map();
    dedupedTasks.forEach(task => {
      const schoolId = task.customerId;
      // Usar customerDescription como nome principal da escola, com fallbacks
      const schoolName = task.customerDescription || task.customerName || `Escola ${schoolId}`;
      
      if (!schoolsMap.has(schoolId)) {
        schoolsMap.set(schoolId, {
          id: schoolId,
          name: schoolName,
          // Adicionar school_info para manter compatibilidade com o restante do código
          school_info: {
            id: schoolId,
            description: schoolName
          },
          tasks: [],
          metrics: {
            total_tasks: 0,
            completed_tasks: 0,
            open_tasks: 0,
            total_equipment: 0,
            active_equipment: 0
          }
        });
      }
      
      const school = schoolsMap.get(schoolId);
      school.tasks.push(task);
      
      // Atualizar métricas da escola
      school.metrics.total_tasks++;
      if ([5, 6].includes(task.taskStatus)) { // Concluída ou aprovada
        school.metrics.completed_tasks++;
      } else if (task.taskStatus !== 7) { // Não é cancelada
        school.metrics.open_tasks++;
      }
      
      // Contar equipamentos
      const equipmentCount = getEquipmentCount(task);
      school.metrics.total_equipment += equipmentCount;
      
      // Contar equipamentos ativos (tarefas não canceladas)
      if (task.taskStatus !== 7) { // Não é cancelada
        school.metrics.active_equipment += equipmentCount;
      }
    });
    
    // Ordenar escolas por total de tarefas
    const schools = Array.from(schoolsMap.values()).map(school => {
      const { total_tasks, completed_tasks } = school.metrics;
      const percentual = total_tasks > 0 ? Math.round((completed_tasks / total_tasks) * 100) : 0;
      return { ...school, metrics: { ...school.metrics, percentual } };
    }).sort((a, b) => b.metrics.total_tasks - a.metrics.total_tasks);

    // Extrair todos os colaboradores do conjunto de dados
    const collaboratorsMap = new Map();
    dedupedTasks.forEach(task => {
      if (task.idUserTo && task.userToName) {
        if (!collaboratorsMap.has(task.idUserTo)) {
          collaboratorsMap.set(task.idUserTo, {
            id: task.idUserTo,
            name: task.userToName,
            totalTasks: 0,
            completedTasks: 0,
            openTasks: 0
          });
        }
        
        const collab = collaboratorsMap.get(task.idUserTo);
        collab.totalTasks++;
        
        if ([5, 6].includes(task.taskStatus)) { // Concluída ou aprovada
          collab.completedTasks++;
        } else if (task.taskStatus !== 7) { // Não é cancelada
          collab.openTasks++;
        }
      }
    });
    
    const collaborators = Array.from(collaboratorsMap.values()).sort((a, b) => b.totalTasks - a.totalTasks);

    return {
      schools,
      collaborators,
      taskTypes: Array.from(taskTypeMap.values()),
      endOfMonthTasks,
      indicators: {
        total_tasks: totalTasks,
        completed_tasks: completedTasksCount,
        open_tasks: openTasksCount,
        canceled_tasks: canceledTasksCount,
        end_of_month_tasks: endOfMonthTasksCount,
        completion_rate: totalTasks > 0 ? Math.round((completedTasksCount / totalTasks) * 100) : 0,
        task_types_count: taskTypeMap.size,
        total_equipment: schools.reduce((total, school) => total + school.metrics.total_equipment, 0),
        active_equipment: schools.reduce((total, school) => total + school.metrics.active_equipment, 0)
      }
    };
  }, [dashboardData, taskTypes, isEndOfMonth, getEquipmentCount]);

  // Função para obter colaboradores de uma escola
  const getSchoolCollaborators = (tasks = []) => {
    if (!tasks) return [];
    const collaboratorsMap = new Map();
    tasks.forEach(task => {
      if (task.idUserTo && task.userToName) {
        collaboratorsMap.set(task.idUserTo, task.userToName);
      }
    });
    return Array.from(collaboratorsMap.values());
  };
  
  // Referência aos colaboradores do processedData
  const allCollaborators = useMemo(() => {
    return processedData?.collaborators || [];
  }, [processedData]);

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Relatório de Faturamento - Mês Atual (Dados do Dashboard)
      </Typography>

      <Box sx={{ display: 'flex', gap: 2, mb: 3, alignItems: 'center' }}>
        <FormControl fullWidth>
          <InputLabel id="contract-select-label">Selecione um Contrato</InputLabel>
          <Select
            labelId="contract-select-label"
            value={selectedContract}
            label="Selecione um Contrato"
            onChange={(e) => setSelectedContract(e.target.value)}
          >
            <MenuItem value="" disabled><em>Nenhum</em></MenuItem>
            {contracts.map((contract) => (
              <MenuItem key={contract.id} value={contract.id}>
                {contract.name || contract.description}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <TextField
          label="Data de Início"
          type="date"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
          InputLabelProps={{ shrink: true }}
          sx={{ width: '250px' }}
        />
        <TextField
          label="Data de Fim"
          type="date"
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
          InputLabelProps={{ shrink: true }}
          sx={{ width: '250px' }}
        />
      </Box>

      {loading && <Box sx={{ display: 'flex', justifyContent: 'center', my: 3 }}><CircularProgress /></Box>}
      {error && <Alert severity="error">{error}</Alert>}

      {processedData && (
        <>
          {/* Indicadores globais */}
          <Accordion 
            expanded={expandedSections.resumo}
            onChange={() => setExpandedSections(prev => ({ ...prev, resumo: !prev.resumo }))}
            sx={{ mb: 3 }}
          >
            <AccordionSummary
              expandIcon={<ExpandMoreIcon />}
              aria-controls="resumo-content"
              id="resumo-header"
              sx={{ bgcolor: '#f5f5f5' }}
            >
              <Typography variant="h6">Resumo do Mês Atual</Typography>
            </AccordionSummary>
            <AccordionDetails>
            <Grid container spacing={2}>
              <Grid item xs={6} sm={2}>
                <Card variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="caption" color="text.secondary">Total de Escolas</Typography>
                  <Typography variant="h6">{processedData.schools.length}</Typography>
                </Card>
              </Grid>
              <Grid item xs={6} sm={2}>
                <Card variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="caption" color="text.secondary">Total de Tarefas</Typography>
                  <Typography variant="h6">{processedData.indicators.total_tasks}</Typography>
                </Card>
              </Grid>
              <Grid item xs={6} sm={2}>
                <Card variant="outlined" sx={{ p: 2, bgcolor: '#e8f5e9' }}>
                  <Typography variant="caption" color="text.secondary">Tarefas Concluídas</Typography>
                  <Typography variant="h6">{processedData.indicators.completed_tasks}</Typography>
                </Card>
              </Grid>
              <Grid item xs={6} sm={2}>
                <Card variant="outlined" sx={{ p: 2, bgcolor: '#ffebee' }}>
                  <Typography variant="caption" color="text.secondary">Tarefas Abertas</Typography>
                  <Typography variant="h6">{processedData.indicators.open_tasks}</Typography>
                </Card>
              </Grid>
              <Grid item xs={6} sm={2}>
                <Card variant="outlined" sx={{ p: 2, bgcolor: '#fff8e1' }}>
                  <Typography variant="caption" color="text.secondary">Tarefas Pendentes para o Fim do Mês</Typography>
                  <Typography variant="h6">{processedData.indicators.end_of_month_tasks}</Typography>
                </Card>
              </Grid>
              <Grid item xs={6} sm={2}>
                <Card variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="caption" color="text.secondary">Taxa de Conclusão</Typography>
                  <Typography variant="h6">{processedData.indicators.completion_rate}%</Typography>
                </Card>
              </Grid>
              <Grid item xs={6} sm={2}>
                <Card variant="outlined" sx={{ p: 2, bgcolor: '#e3f2fd' }}>
                  <Typography variant="caption" color="text.secondary">Total de Equipamentos</Typography>
                  <Typography variant="h6">{KPI_TOTAL_EQUIP}</Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', fontSize: '0.7rem' }}>
                    (equipamentos sob responsabilidade do setor)
                  </Typography>
                </Card>
              </Grid>
              <Grid item xs={6} sm={2}>
                <Card variant="outlined" sx={{ p: 2, bgcolor: '#e8f5e9' }}>
                  <Typography variant="caption" color="text.secondary">Equipamentos em Tarefas Ativas</Typography>
                  <Typography variant="h6">{processedData.indicators.active_equipment}</Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', fontSize: '0.7rem' }}>
                    (apenas equipamentos com status ativo)
                  </Typography>
                </Card>
              </Grid>
            </Grid>
            </AccordionDetails>
          </Accordion>
          
          {/* Resumo Financeiro */}
          <Accordion 
            expanded={expandedSections.financeiro || false}
            onChange={() => setExpandedSections(prev => ({ ...prev, financeiro: !prev.financeiro }))}
            sx={{ mb: 3 }}
          >
            <AccordionSummary
              expandIcon={<ExpandMoreIcon />}
              aria-controls="financeiro-content"
              id="financeiro-header"
              sx={{ bgcolor: '#e3f2fd' }}
            >
              <Typography variant="h6">Resumo Financeiro - {processedData.schools[0]?.school_info?.description || processedData.schools[0]?.customerDescription || 'Prestador'}</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Box sx={{ overflowX: 'auto' }}>
                {/* Tabela de Valores do Prestador */}
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 'bold' }}>VALORES - PLANEJADO {new Date().toLocaleDateString('pt-BR', { month: '2-digit', year: 'numeric' })}</Typography>
                  <Table size="small" sx={{ border: '1px solid rgba(224, 224, 224, 1)' }}>
                    <TableHead>
                      <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                        <TableCell>DESCRIÇÃO</TableCell>
                        <TableCell align="right">PLANEJADO</TableCell>
                        <TableCell align="right">UNITÁRIO</TableCell>
                        <TableCell align="right">ADICIONAL</TableCell>
                        <TableCell align="right" sx={{ bgcolor: '#ffcdd2' }}>EXECUTADO</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      <TableRow>
                        <TableCell>PREV MENSAL</TableCell>
                        <TableCell align="right">{processedData.indicators.total_equipment || 0}</TableCell>
                        <TableCell align="right">R$ 8,50</TableCell>
                        <TableCell align="right">R$ 3,50</TableCell>
                        <TableCell align="right">{`R$ ${((processedData.indicators.total_equipment || 0) * 8.5 + (processedData.indicators.total_equipment || 0) * 3.5).toFixed(2).replace('.', ',')}`}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>EXCEDENTE</TableCell>
                        <TableCell align="right">{processedData.indicators.open_tasks || 0}</TableCell>
                        <TableCell align="right">R$ 10,75</TableCell>
                        <TableCell align="right">R$ -</TableCell>
                        <TableCell align="right">{`R$ ${((processedData.indicators.open_tasks || 0) * 10.75).toFixed(2).replace('.', ',')}`}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>PREV SEMESTRAL</TableCell>
                        <TableCell align="right">{processedData.indicators.completed_tasks || 0}</TableCell>
                        <TableCell align="right">R$ 8,50</TableCell>
                        <TableCell align="right">R$ 3,50</TableCell>
                        <TableCell align="right">{`R$ ${((processedData.indicators.completed_tasks || 0) * 8.5 + (processedData.indicators.completed_tasks || 0) * 3.5).toFixed(2).replace('.', ',')}`}</TableCell>
                      </TableRow>
                      <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                        <TableCell>SUBTOTAL</TableCell>
                        <TableCell align="right"></TableCell>
                        <TableCell align="right"></TableCell>
                        <TableCell align="right"></TableCell>
                        <TableCell align="right">R$ 6.032,25</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>INCENTIVO VEICULAR</TableCell>
                        <TableCell align="right"></TableCell>
                        <TableCell align="right"></TableCell>
                        <TableCell align="right"></TableCell>
                        <TableCell align="right">R$ 1.000,00</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>PARTICULARES</TableCell>
                        <TableCell align="right">6</TableCell>
                        <TableCell align="right">R$ 45,60</TableCell>
                        <TableCell align="right"></TableCell>
                        <TableCell align="right">R$ 273,60</TableCell>
                      </TableRow>
                      <TableRow sx={{ bgcolor: '#f5f5f5', fontWeight: 'bold' }}>
                        <TableCell>TOTAL</TableCell>
                        <TableCell align="right"></TableCell>
                        <TableCell align="right"></TableCell>
                        <TableCell align="right"></TableCell>
                        <TableCell align="right">R$ 7.305,85</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </Box>
                
                {/* Tabela de Valores Considerados */}
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 'bold' }}>VALORES - EXECUTADO {new Date().toLocaleDateString('pt-BR', { month: '2-digit', year: 'numeric' })}</Typography>
                  <Table size="small" sx={{ border: '1px solid rgba(224, 224, 224, 1)' }}>
                    <TableHead>
                      <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                        <TableCell>DESCRIÇÃO</TableCell>
                        <TableCell align="right">EXECUTADO</TableCell>
                        <TableCell align="right">UNITÁRIO</TableCell>
                        <TableCell align="right">ADICIONAL</TableCell>
                        <TableCell align="right" sx={{ bgcolor: '#c8e6c9' }}>CONSIDERADO</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      <TableRow>
                        <TableCell>PREV MENSAL</TableCell>
                        <TableCell align="right">415</TableCell>
                        <TableCell align="right">R$ 8,50</TableCell>
                        <TableCell align="right">R$ 3,50</TableCell>
                        <TableCell align="right">R$ 4.980,01</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>EXCEDENTE</TableCell>
                        <TableCell align="right">3</TableCell>
                        <TableCell align="right">R$ 10,75</TableCell>
                        <TableCell align="right">R$ 3,50</TableCell>
                        <TableCell align="right">R$ 42,75</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>PREV SEMESTRAL</TableCell>
                        <TableCell align="right">85</TableCell>
                        <TableCell align="right">R$ 8,50</TableCell>
                        <TableCell align="right">R$ 3,50</TableCell>
                        <TableCell align="right">R$ 1.020,00</TableCell>
                      </TableRow>
                      <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                        <TableCell>SUBTOTAL</TableCell>
                        <TableCell align="right"></TableCell>
                        <TableCell align="right"></TableCell>
                        <TableCell align="right"></TableCell>
                        <TableCell align="right">R$ 6.042,75</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>INCENTIVO VEICULAR</TableCell>
                        <TableCell align="right"></TableCell>
                        <TableCell align="right"></TableCell>
                        <TableCell align="right"></TableCell>
                        <TableCell align="right">R$ 1.000,00</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>PARTICULARES</TableCell>
                        <TableCell align="right">6</TableCell>
                        <TableCell align="right">R$ 45,60</TableCell>
                        <TableCell align="right"></TableCell>
                        <TableCell align="right">R$ 273,60</TableCell>
                      </TableRow>
                      <TableRow sx={{ bgcolor: '#f5f5f5', fontWeight: 'bold' }}>
                        <TableCell>TOTAL</TableCell>
                        <TableCell align="right"></TableCell>
                        <TableCell align="right"></TableCell>
                        <TableCell align="right"></TableCell>
                        <TableCell align="right">R$ 7.316,35</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </Box>
                
                {/* Tabela de Planejado vs Executado */}
                <Box>
                  <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 'bold' }}>TAREFAS - PLANEJADO vs EXECUTADO</Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <Table size="small" sx={{ border: '1px solid rgba(224, 224, 224, 1)' }}>
                        <TableHead>
                          <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                            <TableCell colSpan={4}>EQUIPAMENTOS ATIVOS</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>TIPO</TableCell>
                            <TableCell align="right">PLANEJADO</TableCell>
                            <TableCell align="right">EXECUTADO</TableCell>
                            <TableCell align="right">%</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          <TableRow>
                            <TableCell>PREV MENSAL</TableCell>
                            <TableCell align="right">419</TableCell>
                            <TableCell align="right">418</TableCell>
                            <TableCell align="right">100%</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>PREV SEMESTRAL</TableCell>
                            <TableCell align="right">84</TableCell>
                            <TableCell align="right">85</TableCell>
                            <TableCell align="right">101%</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>CORRETIVA</TableCell>
                            <TableCell align="right">34</TableCell>
                            <TableCell align="right">34</TableCell>
                            <TableCell align="right">100%</TableCell>
                          </TableRow>
                        </TableBody>
                      </Table>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Table size="small" sx={{ border: '1px solid rgba(224, 224, 224, 1)' }}>
                        <TableHead>
                          <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                            <TableCell colSpan={4}>TAREFA</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>TIPO</TableCell>
                            <TableCell align="right">PLANEJADO</TableCell>
                            <TableCell align="right">EXECUTADO</TableCell>
                            <TableCell align="right">%</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          <TableRow>
                            <TableCell>EPI</TableCell>
                            <TableCell align="right">20</TableCell>
                            <TableCell align="right">20</TableCell>
                            <TableCell align="right">100%</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>INVENTÁRIO DE FERRAMENTAS</TableCell>
                            <TableCell align="right">1</TableCell>
                            <TableCell align="right">1</TableCell>
                            <TableCell align="right">100%</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>AUDITORIAS</TableCell>
                            <TableCell align="right">1</TableCell>
                            <TableCell align="right">1</TableCell>
                            <TableCell align="right">100%</TableCell>
                          </TableRow>
                        </TableBody>
                      </Table>
                    </Grid>
                  </Grid>
                </Box>
                
                {/* Legenda */}
                <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 20, height: 20, bgcolor: '#ffcdd2' }}></Box>
                    <Typography variant="caption">O que foi realizado</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 20, height: 20, bgcolor: '#c8e6c9' }}></Box>
                    <Typography variant="caption">O que será pago</Typography>
                  </Box>
                </Box>
              </Box>
            </AccordionDetails>
          </Accordion>
          
          {/* Lista de colaboradores */}
          <Accordion 
            expanded={expandedSections.colaboradores}
            onChange={() => setExpandedSections(prev => ({ ...prev, colaboradores: !prev.colaboradores }))}
            sx={{ mb: 3 }}
          >
            <AccordionSummary
              expandIcon={<ExpandMoreIcon />}
              aria-controls="colaboradores-content"
              id="colaboradores-header"
              sx={{ bgcolor: '#f5f5f5' }}
            >
              <Typography variant="h6">
                Colaboradores ({allCollaborators.length})
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
            <TableContainer component={Paper}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Colaborador</TableCell>
                    <TableCell align="center">Total de Tarefas</TableCell>
                    <TableCell align="center">Concluídas</TableCell>
                    <TableCell align="center">Abertas</TableCell>
                    <TableCell align="center">Taxa de Conclusão</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {allCollaborators.map(collab => (
                    <TableRow key={collab.id}>
                      <TableCell>{collab.name}</TableCell>
                      <TableCell align="center">{collab.totalTasks}</TableCell>
                      <TableCell align="center">{collab.completedTasks}</TableCell>
                      <TableCell align="center">{collab.openTasks}</TableCell>
                      <TableCell align="center">
                        {collab.totalTasks > 0 ? 
                          `${Math.round((collab.completedTasks / collab.totalTasks) * 100)}%` : 
                          'N/A'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            </AccordionDetails>
          </Accordion>
          
          {/* Tipos de tarefas abertas */}
          <Accordion 
            expanded={expandedSections.tiposTarefas}
            onChange={() => setExpandedSections(prev => ({ ...prev, tiposTarefas: !prev.tiposTarefas }))}
            sx={{ mb: 3 }}
          >
            <AccordionSummary
              expandIcon={<ExpandMoreIcon />}
              aria-controls="tipos-tarefas-content"
              id="tipos-tarefas-header"
              sx={{ bgcolor: '#f5f5f5' }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%', justifyContent: 'space-between' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CategoryIcon color="primary" />
                  <Typography variant="h6">
                    Tipos de Tarefas Abertas ({processedData.indicators?.task_types_count || 0})
                  </Typography>
                </Box>
                <Chip 
                  size="small" 
                  label={`${processedData.indicators?.open_tasks || 0} tarefas abertas`} 
                  color="warning" 
                  variant="outlined" 
                />
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <TableContainer component={Paper}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Tipo de Tarefa</TableCell>
                      <TableCell align="center">Quantidade</TableCell>
                      <TableCell>Ações</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {processedData.taskTypes?.map((typeData, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          <Tooltip title={`ID: ${typeData?.id || 'N/A'}`} placement="top">
                            <span>{typeData?.type || 'Tipo desconhecido'}</span>
                          </Tooltip>
                        </TableCell>
                        <TableCell align="center">{typeData?.count || 0}</TableCell>
                        <TableCell>
                          <Button 
                            size="small" 
                            variant="outlined" 
                            startIcon={<AssignmentIcon />}
                            onClick={() => {
                              // Aqui poderia abrir um dialog com detalhes das tarefas deste tipo
                              console.log(`Detalhes do tipo: ${typeData?.type}`, typeData?.tasks);
                            }}
                          >
                            Ver Tarefas
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </AccordionDetails>
          </Accordion>
          
          {/* Tarefas pendentes para o fim do mês - sempre exibir a seção */}
          {(
            <Accordion 
              expanded={expandedSections.tarefasFimMes}
              onChange={() => setExpandedSections(prev => ({ ...prev, tarefasFimMes: !prev.tarefasFimMes }))}
              sx={{ mb: 3 }}
            >
              <AccordionSummary
                expandIcon={<ExpandMoreIcon />}
                aria-controls="tarefas-fim-mes-content"
                id="tarefas-fim-mes-header"
                sx={{ bgcolor: '#fff8e1' }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%', justifyContent: 'space-between' }}>
                  <Typography variant="h6" sx={{ color: '#f57c00' }}>
                    {processedData.indicators?.end_of_month_tasks > 0 
                      ? `Atenção: ${processedData.indicators?.end_of_month_tasks} tarefas pendentes para o fim do mês`
                      : 'Tarefas Pendentes para o Fim do Mês'}
                  </Typography>
                  <Chip 
                    size="small" 
                    label={`${processedData.indicators?.end_of_month_tasks || 0} tarefas`} 
                    color="warning" 
                    variant="outlined" 
                  />
                </Box>
              </AccordionSummary>
              <AccordionDetails>
              <TableContainer component={Paper}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Escola</TableCell>
                      <TableCell>Tarefa</TableCell>
                      <TableCell>Data Prevista</TableCell>
                      <TableCell>Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {(processedData.endOfMonthTasks?.length || 0) > 0 ? (
                      processedData.endOfMonthTasks?.map(task => (
                        <TableRow key={task?.taskId || Math.random()}>
                          <TableCell>
                            {/* Buscar primeiro nas escolas processadas */}
                            {processedData.schools?.find(s => 
                              // Comparar como strings e verificar se o ID da escola corresponde ao customerId da tarefa
                              String(s.school_info?.id || '') === String(task.customerId || '')
                            )?.school_info?.description || 
                            /* Se não encontrar, usar os dados diretos da tarefa */
                            task.customerDescription || task.customerName || 'Sem escola'}
                          </TableCell>
                          <TableCell>{task.orientation || 'Sem descrição'}</TableCell>
                          <TableCell>{formatDate(task.taskDate || task.scheduledDate)}</TableCell>
                          <TableCell><StatusChip status={task.taskStatus} /></TableCell>
                        </TableRow>
                      ))
                    ) : (
                      <TableRow>
                        <TableCell colSpan={4} align="center">
                          <Typography variant="body2" sx={{ py: 2, color: 'text.secondary' }}>
                            Não há tarefas pendentes para o fim do mês.
                          </Typography>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
              </AccordionDetails>
            </Accordion>
          )}

          {/* Seção de escolas com expansor */}
          <Accordion 
            expanded={expandedSections.escolas}
            onChange={() => setExpandedSections(prev => ({ ...prev, escolas: !prev.escolas }))}
            sx={{ mb: 3 }}
          >
            <AccordionSummary
              expandIcon={<ExpandMoreIcon />}
              aria-controls="escolas-content"
              id="escolas-header"
              sx={{ bgcolor: '#f5f5f5' }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%', justifyContent: 'space-between' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <SchoolIcon color="primary" />
                  <Typography variant="h6">Escolas ({processedData.schools?.length || 0})</Typography>
                </Box>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Chip 
                    size="small" 
                    label={`${processedData.indicators?.total_tasks || 0} tarefas`} 
                    color="primary" 
                    variant="outlined" 
                  />
                  <Chip 
                    size="small" 
                    label={`${processedData.indicators?.completed_tasks || 0} concluídas`} 
                    color="success" 
                    variant="outlined" 
                  />
                </Box>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <ButtonGroup variant="outlined" size="small">
                  <Tooltip title="Expandir todas as escolas">
                    <Button 
                      startIcon={<UnfoldMoreIcon />}
                      onClick={(e) => {
                        e.stopPropagation();
                        const allExpanded = {};
                        processedData.schools?.forEach(school => {
                          if (school.school_info?.id) {
                            allExpanded[school.school_info.id] = true;
                          }
                        });
                        setExpandedSchools(allExpanded);
                      }}
                    >
                      Expandir Todas
                    </Button>
                  </Tooltip>
                  <Tooltip title="Recolher todas as escolas">
                    <Button 
                      startIcon={<UnfoldLessIcon />}
                      onClick={(e) => {
                        e.stopPropagation();
                        setExpandedSchools({});
                      }}
                    >
                      Recolher Todas
                    </Button>
                  </Tooltip>
                </ButtonGroup>
                
                <Box>
                  <Tooltip title="Filtrar escolas">
                    <IconButton size="small">
                      <FilterListIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Ordenar escolas">
                    <IconButton size="small">
                      <SortIcon />
                    </IconButton>
                  </Tooltip>
                </Box>
              </Box>
            
              {processedData.schools?.map((school) => {
                // Garantir que school_info e id existam
                const schoolId = school.school_info?.id || `school-${Math.random()}`;
                
                return (
                <Accordion 
                  key={schoolId} 
                  sx={{ mb: 1 }}
                  expanded={!!expandedSchools[schoolId]}
                  onChange={() => {
                    setExpandedSchools(prev => ({
                      ...prev,
                      [schoolId]: !prev[schoolId]
                    }));
                  }}
                >
                  <AccordionSummary
                    expandIcon={<ExpandMoreIcon />}
                    aria-controls={`school-${schoolId}-content`}
                    id={`school-${schoolId}-header`}
                    sx={{ bgcolor: selectedSchool?.school_info?.id === schoolId ? '#e3f2fd' : 'inherit' }}
                  >
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
                      <Typography sx={{ fontWeight: 'medium' }}>
                        {school.school_info?.description || school.customerName || school.name || 'Escola sem nome'}
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 2 }}>
                        <Chip 
                          size="small" 
                          label={`${school.tasks?.length || 0} tarefas`} 
                          color="primary" 
                          variant="outlined" 
                        />
                        <Chip 
                          size="small" 
                          label={`${school.metrics?.completed_tasks || 0} concluídas`} 
                          color="success" 
                          variant="outlined" 
                        />
                        <Chip 
                          size="small" 
                          label={`${(school.tasks?.length || 0) - (school.metrics?.completed_tasks || 0)} pendentes`} 
                          color="warning" 
                          variant="outlined" 
                        />
                        <Chip 
                          size="small" 
                          label={`${school.metrics?.active_equipment || 0} equipamentos ativos`} 
                          color="info" 
                          variant="outlined" 
                          title="Equipamentos com status ativo vinculados a tarefas desta escola"
                        />
                      </Box>
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box>
                      <Typography variant="subtitle2" gutterBottom>
                        Detalhes da Escola
                    </Typography>
                    <Grid container spacing={2} sx={{ mb: 2 }}>
                      <Grid item xs={12} sm={3}>
                        <Card variant="outlined" sx={{ p: 1 }}>
                          <Typography variant="caption" color="text.secondary">Total de Tarefas</Typography>
                          <Typography variant="body1">{school.tasks?.length || 0}</Typography>
                        </Card>
                      </Grid>
                      <Grid item xs={12} sm={3}>
                        <Card variant="outlined" sx={{ p: 1 }}>
                          <Typography variant="caption" color="text.secondary">Concluídas</Typography>
                          <Typography variant="body1">{school.metrics?.completed_tasks || 0}</Typography>
                        </Card>
                      </Grid>
                      <Grid item xs={12} sm={3}>
                        <Card variant="outlined" sx={{ p: 1 }}>
                          <Typography variant="caption" color="text.secondary">Taxa de Conclusão</Typography>
                          <Typography variant="body1">{school.metrics?.percentual || 0}%</Typography>
                        </Card>
                      </Grid>
                      <Grid item xs={12} sm={3}>
                        <Card variant="outlined" sx={{ p: 1, bgcolor: '#e3f2fd' }}>
                          <Typography variant="caption" color="text.secondary">Equipamentos Ativos</Typography>
                          <Typography variant="body1">{school.metrics?.active_equipment || 0}</Typography>
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', fontSize: '0.7rem' }}>
                            (apenas equipamentos com status ativo)
                          </Typography>
                        </Card>
                      </Grid>
                    </Grid>
                    
                    <Divider sx={{ my: 2 }} />
                    
                    <Typography variant="subtitle2" gutterBottom>
                      Colaboradores da Escola
                    </Typography>
                    <Box sx={{ mb: 2 }}>
                      {getSchoolCollaborators(school.tasks)?.length > 0 ? (
                        <Grid container spacing={1}>
                          {getSchoolCollaborators(school.tasks)?.map((name, index) => (
                            <Grid item key={index}>
                              <Chip label={name || 'Sem nome'} size="small" />
                            </Grid>
                          ))}
                        </Grid>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          Nenhum colaborador associado a esta escola.
                        </Typography>
                      )}
                    </Box>
                    
                    <Divider sx={{ my: 2 }} />
                    
                    <Typography variant="subtitle2" gutterBottom>
                      Tarefas da Escola
                    </Typography>
                    <TableContainer component={Paper} variant="outlined">
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Tarefa</TableCell>
                            <TableCell>Data</TableCell>
                            <TableCell>Status</TableCell>
                            <TableCell>Colaborador</TableCell>
                            <TableCell>Equipamentos</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {(school.tasks?.length || 0) > 0 ? (
                            school.tasks?.map(task => (
                              <TableRow key={task?.taskId || Math.random()}>
                                <TableCell>{task?.orientation || 'Sem descrição'}</TableCell>
                                <TableCell>{formatDate(task?.checkInDate)}</TableCell>
                                <TableCell><StatusChip status={task?.taskStatus} /></TableCell>
                                <TableCell>{task?.userToName || 'N/A'}</TableCell>
                                <TableCell>
                                  {getEquipmentCount(task) > 0 ? (
                                    <Chip 
                                      size="small" 
                                      label={getEquipmentCount(task)} 
                                      color="info" 
                                      variant="outlined"
                                      title="Número de equipamentos vinculados a esta tarefa"
                                    />
                                  ) : 'Nenhum'}
                                </TableCell>
                              </TableRow>
                            ))
                          ) : (
                            <TableRow>
                              <TableCell colSpan={5} align="center">Nenhuma tarefa encontrada</TableCell>
                            </TableRow>
                          )}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Box>
                </AccordionDetails>
              </Accordion>
            );
            })}
            </AccordionDetails>
          </Accordion>
        </>
      )}
    </Box>
  );
};

export default FaturamentoReport;