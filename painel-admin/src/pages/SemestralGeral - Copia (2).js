import React, { useState, useEffect } from 'react';
import {
  Box, Grid, Paper, Typography, MenuItem, FormControl, Select, InputLabel, 
  CircularProgress, Alert, Table, TableBody, TableCell, TableContainer, 
  TableHead, TableRow, Card, TextField, Button, IconButton, Tooltip, Chip,
  Popover, List, ListItem, ListItemText
} from '@mui/material';
import CalendarViewWeekIcon from '@mui/icons-material/CalendarViewWeek';
import LinkIcon from '@mui/icons-material/Link';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import axios from 'axios';

// Registrar componentes do Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  ChartTooltip,
  Legend
);

const API_BASE_URL = 'http://127.0.0.1:8000/api';

// IDs dos contratos de Santos (SETOR 01 a SETOR 05)
const SANTOS_CONTRACT_IDS = [156750, 156751, 156752, 156753, 156754];

// IDs das tarefas semestrais baseado no Dashboard.js
const SEMESTRAL_TASK_IDS = [175652]; // Preventiva Semestral
const SEMESTRAL_KEYWORDS = ['semestral', 'preventiva semestral'];

const KpiCard = ({ title, value, icon, extra = null }) => (
  <Card variant="outlined" sx={{ p: 2, height: '100%' }}>
    <Box sx={{ 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'space-between'
    }}>
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        {icon}
        <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
          {title}
        </Typography>
      </Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
        <Typography variant="h6" sx={{ fontWeight: 'bold' }}>{value}</Typography>
        {extra}
      </Box>
    </Box>
  </Card>
);

const isInPeriod = (dateLike, start, end) => {
  const d = new Date(dateLike);
  if (isNaN(d)) return false;
  const startDate = new Date(start);
  const endDate = new Date(end);
  return d >= startDate && d <= endDate;
};

const isSemestralTask = (task) => {
  const orientation = (task.orientation || '').toLowerCase();
  const matchesKeyword = SEMESTRAL_KEYWORDS.some(k => orientation.includes(k));
  const matchesId = SEMESTRAL_TASK_IDS.includes(task.taskType);
  return matchesKeyword || matchesId;
};

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return 'Data inválida';
  return date.toLocaleDateString('pt-BR');
};

const getDayOfMonth = (dateString) => {
  if (!dateString) return 0;
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return 0;
  return date.getDate();
};

const SemestralGeral = () => {
  // Configurar datas para o mês atual (primeiro e último dia)
  const today = new Date();
  const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
  const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);
  
  const [dateRange, setDateRange] = useState({
    start: firstDay.toISOString().slice(0, 10),
    end: lastDay.toISOString().slice(0, 10),
  });
  
  const [selectedContract, setSelectedContract] = useState('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [contracts, setContracts] = useState([]);
  const [semestralData, setSemestralData] = useState([]);
  const [dailyStats, setDailyStats] = useState({});
  const [tasksByDay, setTasksByDay] = useState({}); // Para armazenar tarefas por dia
  const [popoverState, setPopoverState] = useState({ open: false, anchorEl: null, tasks: [] });

  // Buscar contratos de Santos
  useEffect(() => {
    const fetchContracts = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/contracts`);
        const allContracts = response.data || [];
        
        // Filtrar apenas os contratos de Santos
        const santosContracts = allContracts.filter(contract => 
          SANTOS_CONTRACT_IDS.includes(contract.id)
        );
        
        const withAll = [
          { id: 'all', description: 'Todos os Setores', name: 'Todos os Setores' }, 
          ...santosContracts
        ];
        
        setContracts(withAll);
        setSelectedContract('all');
      } catch (err) {
        setError('Falha ao buscar contratos.');
        console.error(err);
      }
    };
    fetchContracts();
  }, []);

  const fetchSemestralData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const contractsToFetch = selectedContract === 'all' 
        ? contracts.filter(c => c.id !== 'all')
        : contracts.filter(c => c.id === selectedContract);

      const allData = [];
      const dailyStatsTemp = {};
      const tasksByDayTemp = {};

      for (const contract of contractsToFetch) {
        const params = {
          start_date: dateRange.start,
          end_date: dateRange.end,
        };

        const response = await axios.get(`${API_BASE_URL}/dashboard/${contract.id}`, { params });
        const schools = response.data.schools || [];

        // Processar tarefas semestrais
        const semestralTasks = [];
        
        schools.forEach(school => {
          if (school.tasks) {
            school.tasks.forEach(task => {
              const dateRef = task.checkInDate || task.lastUpdate;
              
              if (dateRef && 
                  isInPeriod(dateRef, dateRange.start, dateRange.end) && 
                  isSemestralTask(task)) {
                
                const taskWithDetails = {
                  ...task,
                  schoolName: school.name,
                  contractName: contract.description || contract.name,
                  contractId: contract.id,
                  day: getDayOfMonth(dateRef)
                };
                
                semestralTasks.push(taskWithDetails);

                // Estatísticas por dia
                const day = getDayOfMonth(dateRef);
                if (!dailyStatsTemp[contract.id]) {
                  dailyStatsTemp[contract.id] = {};
                }
                if (!dailyStatsTemp[contract.id][day]) {
                  dailyStatsTemp[contract.id][day] = 0;
                }
                dailyStatsTemp[contract.id][day]++;
                
                // Armazenar tarefas por dia para o popover
                const dayKey = `${contract.id}-${day}`;
                if (!tasksByDayTemp[dayKey]) {
                  tasksByDayTemp[dayKey] = [];
                }
                tasksByDayTemp[dayKey].push(taskWithDetails);
              }
            });
          }
        });

        allData.push({
          contractId: contract.id,
          contractName: contract.description || contract.name,
          tasks: semestralTasks,
          totalTasks: semestralTasks.length,
          completedTasks: semestralTasks.filter(t => [5, 6].includes(t.taskStatus)).length
        });
      }

      setSemestralData(allData);
      setDailyStats(dailyStatsTemp);
      setTasksByDay(tasksByDayTemp);
      
    } catch (err) {
      setError('Erro ao buscar dados semestrais.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (contracts.length > 0) {
      fetchSemestralData();
    }
  }, [dateRange, selectedContract, contracts]); // eslint-disable-line react-hooks/exhaustive-deps

  // Calcular totais gerais
  const totalTasks = semestralData.reduce((sum, contract) => sum + contract.totalTasks, 0);
  const totalCompleted = semestralData.reduce((sum, contract) => sum + contract.completedTasks, 0);
  const completionRate = totalTasks > 0 ? Math.round((totalCompleted / totalTasks) * 100) : 0;

  // Gerar dias únicos para a tabela
  const allDays = new Set();
  Object.values(dailyStats).forEach(contractStats => {
    Object.keys(contractStats).forEach(day => allDays.add(parseInt(day)));
  });
  const sortedDays = Array.from(allDays).sort((a, b) => a - b);

  // Organizar dados por setor e data para a tabela detalhada
  const organizeTasksByContract = () => {
    const organized = {};
    
    semestralData.forEach(contract => {
      organized[contract.contractId] = {
        contractName: contract.contractName,
        tasksByDate: {}
      };
      
      // Agrupar tarefas por data
      contract.tasks.forEach(task => {
        const dateKey = task.checkInDate || task.lastUpdate;
        const dateFormatted = formatDate(dateKey);
        
        if (!organized[contract.contractId].tasksByDate[dateFormatted]) {
          organized[contract.contractId].tasksByDate[dateFormatted] = {
            day: task.day,
            tasks: [],
            date: dateKey
          };
        }
        
        organized[contract.contractId].tasksByDate[dateFormatted].tasks.push(task);
      });
      
      // Ordenar datas dentro de cada contrato
      const sortedDates = Object.keys(organized[contract.contractId].tasksByDate)
        .sort((a, b) => {
          const dateA = new Date(organized[contract.contractId].tasksByDate[a].date);
          const dateB = new Date(organized[contract.contractId].tasksByDate[b].date);
          return dateA - dateB;
        });
      
      const sortedTasksByDate = {};
      sortedDates.forEach(date => {
        sortedTasksByDate[date] = organized[contract.contractId].tasksByDate[date];
      });
      organized[contract.contractId].tasksByDate = sortedTasksByDate;
    });
    
    return organized;
  };
  
  const organizedTasks = organizeTasksByContract();

  // Preparar dados para o gráfico Chart.js
  const prepareChartData = () => {
    const labels = [];
    const datasets = [];
    
    // Criar labels (dias)
    sortedDays.forEach(day => {
      if (Object.values(dailyStats).some(contractStats => contractStats[day] > 0)) {
        labels.push(`Dia ${day}`);
      }
    });
    
    // Cores para cada setor (mais vibrantes e distintas)
    const sectorColors = {
      'SETOR 01': '#8884d8',  // Roxo
      'SETOR 02': '#82ca9d',  // Verde
      'SETOR 03': '#ffc658',  // Amarelo/Laranja
      'SETOR 04': '#ff7c7c',  // Vermelho/Rosa
      'SETOR 05': '#8dd1e1'   // Azul claro
    };
    
    const sectorBorderColors = {
      'SETOR 01': '#6b5b95',  // Roxo escuro
      'SETOR 02': '#5a9b7a',  // Verde escuro
      'SETOR 03': '#e6a84a',  // Amarelo escuro
      'SETOR 04': '#e55a5a',  // Vermelho escuro
      'SETOR 05': '#7ab8c7'   // Azul escuro
    };
    
    // Criar datasets (um para cada setor)
    semestralData.forEach((contract, index) => {
      const contractName = contract.contractName.replace('STS366932/22 - ', '');
      const data = [];
      
      labels.forEach(label => {
        const day = parseInt(label.replace('Dia ', ''));
        const count = dailyStats[contract.contractId]?.[day] || 0;
        data.push(count);
      });
      
      if (data.some(value => value > 0)) {
        // Array de cores fixas para garantir que funcione
        const colorArray = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1'];
        const borderColorArray = ['#6b5b95', '#5a9b7a', '#e6a84a', '#e55a5a', '#7ab8c7'];
        
        console.log('Contract:', contractName, 'Color:', sectorColors[contractName] || colorArray[index % 5]);
        
        datasets.push({
          label: contractName,
          data: data,
          backgroundColor: sectorColors[contractName] || colorArray[index % 5],
          borderColor: sectorBorderColors[contractName] || borderColorArray[index % 5],
          borderWidth: 2
        });
      }
    });
    
    return { labels, datasets };
  };

  const chartData = prepareChartData();
  
  // Opções do gráfico
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Distribuição de Tarefas Semestrais por Dia e Setor'
      },
    },
    scales: {
      x: {
        stacked: true,
        title: {
          display: true,
          text: 'Dias do Mês'
        }
      },
      y: {
        stacked: true,
        beginAtZero: true,
        title: {
          display: true,
          text: 'Quantidade de Tarefas'
        },
        ticks: {
          stepSize: 1
        }
      },
    },
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <CalendarViewWeekIcon />
        Semestral Geral - Santos
      </Typography>

      {/* Filtros */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Contrato</InputLabel>
              <Select
                value={selectedContract}
                onChange={(e) => setSelectedContract(e.target.value)}
                label="Contrato"
              >
                {contracts.map(contract => (
                  <MenuItem key={contract.id} value={contract.id}>
                    {contract.description || contract.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} md={3}>
            <TextField
              fullWidth
              type="date"
              label="Data Início"
              value={dateRange.start}
              onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          
          <Grid item xs={12} md={3}>
            <TextField
              fullWidth
              type="date"
              label="Data Fim"
              value={dateRange.end}
              onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          
          <Grid item xs={12} md={3}>
            <Button 
              variant="contained" 
              onClick={fetchSemestralData}
              disabled={loading}
              fullWidth
            >
              Atualizar
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* KPIs */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <KpiCard
            title="Total de Tarefas Semestrais"
            value={totalTasks}
            icon={<CalendarViewWeekIcon color="primary" />}
          />
        </Grid>
        <Grid item xs={12} md={4}>
          <KpiCard
            title="Tarefas Concluídas"
            value={totalCompleted}
            icon={<CalendarViewWeekIcon color="success" />}
          />
        </Grid>
        <Grid item xs={12} md={4}>
          <KpiCard
            title="Taxa de Conclusão"
            value={`${completionRate}%`}
            icon={<CalendarViewWeekIcon color="info" />}
          />
        </Grid>
      </Grid>

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Gráfico de Contagem por Dia */}
      {!loading && chartData.labels && chartData.labels.length > 0 && (
        <Paper sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
            Gráfico de Tarefas Semestrais por Dia
          </Typography>
          <Box sx={{ p: 2, height: 400 }}>
            <Bar data={chartData} options={chartOptions} />
          </Box>
        </Paper>
      )}

      {/* Tabela de Contagem por Dia */}
      {!loading && sortedDays.length > 0 && (
        <Paper sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
            Contagem de Tarefas Semestrais por Dia
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Setor</strong></TableCell>
                  {sortedDays.map(day => (
                    <TableCell key={day} align="center">
                      <strong>Dia {day}</strong>
                    </TableCell>
                  ))}
                  <TableCell align="center"><strong>Total</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {semestralData.map(contract => (
                  <TableRow key={contract.contractId}>
                    <TableCell>{contract.contractName}</TableCell>
                    {sortedDays.map(day => {
                    const count = dailyStats[contract.contractId]?.[day] || 0;
                    const dayKey = `${contract.contractId}-${day}`;
                    const tasksForDay = tasksByDay[dayKey] || [];
                    
                    return (
                      <TableCell key={day} align="center">
                        {count > 0 ? (
                          <Tooltip 
                            title={`${count} tarefa${count > 1 ? 's' : ''} - Clique para ver detalhes`}
                            arrow
                          >
                            <Typography 
                              variant="body2" 
                              sx={{ 
                                cursor: 'pointer', 
                                color: 'primary.main',
                                fontWeight: 'bold',
                                '&:hover': {
                                  backgroundColor: 'action.hover',
                                  borderRadius: 1,
                                  px: 1
                                }
                              }}
                              onClick={(event) => {
                                setPopoverState({
                                  open: true,
                                  anchorEl: event.currentTarget,
                                  tasks: tasksForDay
                                });
                              }}
                            >
                              {count}
                            </Typography>
                          </Tooltip>
                        ) : (
                          <Typography variant="body2" color="text.disabled">
                            0
                          </Typography>
                        )}
                      </TableCell>
                    );
                  })}
                    <TableCell align="center">
                      <strong>{contract.totalTasks}</strong>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* Lista Detalhada de Tarefas Organizadas */}
      {!loading && semestralData.length > 0 && (
        <Paper>
          <Typography variant="h6" sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
            Detalhamento das Tarefas Semestrais (Organizadas por Setor e Data)
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Setor</TableCell>
                  <TableCell>Data</TableCell>
                  <TableCell>Dia</TableCell>
                  <TableCell>Qtd Tarefas</TableCell>
                  <TableCell>Escolas/Tarefas</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Links</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {Object.keys(organizedTasks)
                  .sort((a, b) => {
                    // Ordenar por nome do contrato
                    const nameA = organizedTasks[a].contractName;
                    const nameB = organizedTasks[b].contractName;
                    return nameA.localeCompare(nameB);
                  })
                  .map(contractId => {
                    const contract = organizedTasks[contractId];
                    return Object.keys(contract.tasksByDate).map((dateFormatted, index) => {
                      const dateData = contract.tasksByDate[dateFormatted];
                      const tasks = dateData.tasks;
                      // const completedTasks = tasks.filter(t => [5, 6].includes(t.taskStatus)).length;
                      
                      return (
                        <TableRow key={`${contractId}-${dateFormatted}`}>
                          <TableCell>
                            {index === 0 ? contract.contractName : ''}
                          </TableCell>
                          <TableCell>{dateFormatted}</TableCell>
                          <TableCell align="center">{dateData.day}</TableCell>
                          <TableCell align="center">{tasks.length}</TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                              {tasks.map((task, taskIndex) => (
                                <Typography key={taskIndex} variant="body2">
                                  <strong>{task.schoolName}</strong>: {task.orientation || 'N/A'}
                                </Typography>
                              ))}
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                              {tasks.map((task, taskIndex) => (
                                <Chip 
                                  key={taskIndex}
                                  label={task.taskStatus === 5 || task.taskStatus === 6 ? 'Concluída' : 'Pendente'}
                                  color={task.taskStatus === 5 || task.taskStatus === 6 ? 'success' : 'default'}
                                  size="small"
                                />
                              ))}
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                              {tasks.map((task, taskIndex) => (
                                <Box key={taskIndex}>
                                  {task.taskUrl ? (
                                    <Tooltip title={`Abrir tarefa ${taskIndex + 1} no Auvo`}>
                                      <IconButton 
                                        size="small" 
                                        onClick={() => window.open(task.taskUrl, '_blank')}
                                        color="primary"
                                      >
                                        <LinkIcon />
                                      </IconButton>
                                    </Tooltip>
                                  ) : (
                                    <Typography variant="body2" color="text.disabled">
                                      N/A
                                    </Typography>
                                  )}
                                </Box>
                              ))}
                            </Box>
                          </TableCell>
                        </TableRow>
                      );
                    });
                  })
                }
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {!loading && semestralData.length === 0 && (
        <Alert severity="info">
          Nenhuma tarefa semestral encontrada no período selecionado.
        </Alert>
      )}
      
      {/* Popover para mostrar detalhes das tarefas */}
      <Popover
        open={popoverState.open}
        anchorEl={popoverState.anchorEl}
        onClose={() => setPopoverState({ ...popoverState, open: false })}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'center',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'center',
        }}
      >
        <Box sx={{ p: 2, maxWidth: 400 }}>
          <Typography variant="h6" gutterBottom>
            Tarefas do Dia ({popoverState.tasks.length})
          </Typography>
          <List dense>
            {popoverState.tasks.map((task, index) => (
              <ListItem key={index} sx={{ px: 0 }}>
                <Box sx={{ width: '100%' }}>
                  <ListItemText
                    primary={`${task.schoolName}`}
                    secondary={task.orientation || 'N/A'}
                  />
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 1 }}>
                    <Chip 
                      label={task.taskStatus === 5 || task.taskStatus === 6 ? 'Concluída' : 'Pendente'}
                      color={task.taskStatus === 5 || task.taskStatus === 6 ? 'success' : 'default'}
                      size="small"
                    />
                    {task.taskUrl && (
                      <Tooltip title="Abrir tarefa no Auvo">
                        <IconButton 
                          size="small" 
                          onClick={() => window.open(task.taskUrl, '_blank')}
                          color="primary"
                        >
                          <LinkIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                  </Box>
                </Box>
              </ListItem>
            ))}
          </List>
        </Box>
      </Popover>
    </Box>
  );
};

export default SemestralGeral;
