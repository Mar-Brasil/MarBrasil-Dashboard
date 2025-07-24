import React, { useState, useEffect } from 'react';
import {
  Box, Grid, Paper, Typography, MenuItem, FormControl, Select, InputLabel, 
  CircularProgress, Alert, Table, TableBody, TableCell, TableContainer, 
  TableHead, TableRow, Card, TextField, Button, IconButton, Tooltip, Chip,
  Popover, List, ListItem, ListItemText
} from '@mui/material';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
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
import ChartDataLabels from 'chartjs-plugin-datalabels';
import { Bar } from 'react-chartjs-2';
import axios from 'axios';

// Registrar componentes do Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  ChartTooltip,
  Legend,
  ChartDataLabels
);

const API_BASE_URL = 'http://127.0.0.1:8000/api';

// IDs dos contratos de Santos (SETOR 01 a SETOR 05)
const SANTOS_CONTRACT_IDS = [156750, 156751, 156752, 156753, 156754];

// IDs das tarefas mensais baseado no Dashboard.js
const MENSAL_TASK_IDS = [175644, 175648, 175656]; // Preventiva Mensal
const MENSAL_KEYWORDS = ['mensal', 'preventiva mensal'];

const KpiCard = ({ title, value, icon, extra = null }) => (
  <Card variant="outlined" sx={{ p: 2, height: '100%' }}>
    <Box sx={{ 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'space-between'
    }}>
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        {icon && <Box sx={{ mr: 1, color: 'primary.main' }}>{icon}</Box>}
        <Box>
          <Typography variant="h6" component="div">
            {value}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {title}
          </Typography>
          {extra && (
            <Typography variant="caption" color="text.secondary">
              {extra}
            </Typography>
          )}
        </Box>
      </Box>
    </Box>
  </Card>
);

const isInPeriod = (dateLike, start, end) => {
  if (!dateLike) return false;
  const date = new Date(dateLike);
  const startDate = new Date(start);
  const endDate = new Date(end);
  return date >= startDate && date <= endDate;
};

const isMensalTask = (task) => {
  return MENSAL_TASK_IDS.includes(task.taskTypeId) || 
         MENSAL_KEYWORDS.some(keyword => 
           task.orientation?.toLowerCase().includes(keyword)
         );
};

const formatDate = (dateString) => {
  if (!dateString) return 'Data não disponível';
  const date = new Date(dateString);
  return date.toLocaleDateString('pt-BR');
};

const getDayOfMonth = (dateString) => {
  if (!dateString) return null;
  const date = new Date(dateString);
  return date.getDate();
};

export default function MensalGeral() {
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
  const [mensalData, setMensalData] = useState([]);
  const [dailyStats, setDailyStats] = useState({});
  const [tasksByDay, setTasksByDay] = useState({});
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

  const fetchMensalData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const contractsToFetch = selectedContract === 'all' 
        ? contracts.filter(c => c.id !== 'all')
        : contracts.filter(c => c.id === selectedContract);

      const allData = [];
      const dailyStatsTemp = {};
      const tasksByDayTemp = {};
      const dailyEquipmentsTemp = {}; // Para contar equipamentos únicos por dia

      for (const contract of contractsToFetch) {
        const params = {
          start_date: dateRange.start,
          end_date: dateRange.end,
        };

        const response = await axios.get(`${API_BASE_URL}/dashboard/${contract.id}`, { params });
        const schools = response.data.schools || [];

        // Processar tarefas mensais
        const mensalTasks = [];
        
        schools.forEach(school => {
          if (school.tasks) {
            school.tasks.forEach(task => {
              const dateRef = task.checkInDate || task.lastUpdate;
              
              if (dateRef && 
                  isInPeriod(dateRef, dateRange.start, dateRange.end) && 
                  isMensalTask(task)) {
                
                const taskWithDetails = {
                  ...task,
                  schoolName: school.school_info?.description || 'Escola não identificada',
                  contractName: contract.description || contract.name,
                  contractId: contract.id,
                  day: getDayOfMonth(dateRef)
                };
                
                mensalTasks.push(taskWithDetails);

                // Estatísticas por dia - contar equipamentos únicos
                const day = getDayOfMonth(dateRef);
                
                // Inicializar estruturas se não existirem
                if (!dailyEquipmentsTemp[contract.id]) {
                  dailyEquipmentsTemp[contract.id] = {};
                }
                if (!dailyEquipmentsTemp[contract.id][day]) {
                  dailyEquipmentsTemp[contract.id][day] = new Set();
                }
                
                // Extrair IDs dos equipamentos da tarefa
                try {
                  const equipmentsIdStr = task.equipmentsId || '[]';
                  const equipmentIds = JSON.parse(equipmentsIdStr);
                  if (Array.isArray(equipmentIds)) {
                    equipmentIds.forEach(equipId => {
                      dailyEquipmentsTemp[contract.id][day].add(equipId);
                    });
                  }
                } catch (error) {
                  console.warn('Erro ao processar equipmentsId:', task.equipmentsId, error);
                }
                
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

        // Calcular total de equipamentos únicos para este contrato
        const allEquipmentIds = new Set();
        mensalTasks.forEach(task => {
          try {
            const equipmentsIdStr = task.equipmentsId || '[]';
            const equipmentIds = JSON.parse(equipmentsIdStr);
            if (Array.isArray(equipmentIds)) {
              equipmentIds.forEach(equipId => allEquipmentIds.add(equipId));
            }
          } catch (error) {
            // Ignorar erros de parse
          }
        });

        allData.push({
          contractId: contract.id,
          contractName: contract.description || contract.name,
          tasks: mensalTasks,
          totalTasks: mensalTasks.length,
          totalEquipments: allEquipmentIds.size, // Total de equipamentos únicos
          completedTasks: mensalTasks.filter(t => [5, 6].includes(t.taskStatus)).length
        });
      }

      // Converter Sets de equipamentos para números
      Object.keys(dailyEquipmentsTemp).forEach(contractId => {
        if (!dailyStatsTemp[contractId]) {
          dailyStatsTemp[contractId] = {};
        }
        Object.keys(dailyEquipmentsTemp[contractId]).forEach(day => {
          dailyStatsTemp[contractId][day] = dailyEquipmentsTemp[contractId][day].size;
        });
      });

      setMensalData(allData);
      setDailyStats(dailyStatsTemp);
      setTasksByDay(tasksByDayTemp);
      
    } catch (err) {
      setError('Erro ao buscar dados mensais.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (contracts.length > 0) {
      fetchMensalData();
    }
  }, [dateRange, selectedContract, contracts]); // eslint-disable-line react-hooks/exhaustive-deps

  // Calcular totais gerais
  const totalTasks = mensalData.reduce((sum, contract) => sum + contract.totalTasks, 0);
  const totalEquipments = mensalData.reduce((sum, contract) => sum + (contract.totalEquipments || 0), 0);
  const totalCompleted = mensalData.reduce((sum, contract) => sum + contract.completedTasks, 0);
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
    
    mensalData.forEach(contract => {
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

  // Mapeamento fixo de cor para rótulo (definido globalmente)
  const colorToLabel = {
    '#8884d8': 'Setor 1',  // Roxo
    '#82ca9d': 'Setor 2',  // Verde
    '#ffc658': 'Setor 3',  // Amarelo/Laranja
    '#ff7c7c': 'Setor 4',  // Vermelho/Rosa
    '#8dd1e1': 'Setor 5'   // Azul claro
  };

  // Mapeamento de nome do setor para cor
  const getSectorColor = (contractName) => {
    if (contractName.includes('SETOR 01')) return '#8884d8'; // Roxo
    if (contractName.includes('SETOR 02')) return '#82ca9d'; // Verde
    if (contractName.includes('SETOR 03')) return '#ffc658'; // Amarelo/Laranja
    if (contractName.includes('SETOR 04')) return '#ff7c7c'; // Vermelho/Rosa
    if (contractName.includes('SETOR 05')) return '#8dd1e1'; // Azul claro
    return '#666666'; // Cor padrão para outros casos
  };

  // Mapeamento de nome do setor para cor de fundo (mais suave)
  const getSectorBackgroundColor = (contractName) => {
    if (contractName.includes('SETOR 01')) return 'rgba(136, 132, 216, 0.15)'; // Roxo suave
    if (contractName.includes('SETOR 02')) return 'rgba(130, 202, 157, 0.15)'; // Verde suave
    if (contractName.includes('SETOR 03')) return 'rgba(255, 198, 88, 0.15)'; // Amarelo/Laranja suave
    if (contractName.includes('SETOR 04')) return 'rgba(255, 124, 124, 0.15)'; // Vermelho/Rosa suave
    if (contractName.includes('SETOR 05')) return 'rgba(141, 209, 225, 0.15)'; // Azul claro suave
    return 'rgba(102, 102, 102, 0.15)'; // Cor padrão suave
  };

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

    // Cores para cada setor (mesmas do gráfico semestral)
    const sectorColors = [
      '#8884d8', // Roxo - SETOR 01
      '#82ca9d', // Verde - SETOR 02  
      '#ffc658', // Amarelo/Laranja - SETOR 03
      '#ff7c7c', // Vermelho/Rosa - SETOR 04
      '#8dd1e1'  // Azul claro - SETOR 05
    ];

    // Criar datasets para cada contrato
    mensalData.forEach((contract, index) => {
      const data = [];
      
      sortedDays.forEach(day => {
        if (Object.values(dailyStats).some(contractStats => contractStats[day] > 0)) {
          data.push(dailyStats[contract.contractId]?.[day] || 0);
        }
      });

      datasets.push({
        label: contract.contractName,
        data: data,
        backgroundColor: sectorColors[index % sectorColors.length],
        borderColor: sectorColors[index % sectorColors.length],
        borderWidth: 2,
      });
    });

    return { labels, datasets };
  };

  const chartData = prepareChartData();

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Distribuição de Tarefas Mensais por Dia e Setor'
      },
      datalabels: {
        display: function(context) {
          // Verificações de segurança
          if (!context || !context.parsed || typeof context.parsed.y === 'undefined') {
            return false;
          }
          return context.parsed.y > 0; // Só mostra se o valor for maior que 0
        },
        color: 'white',
        font: {
          weight: 'bold',
          size: 11
        },
        formatter: function(value, context) {
          // Verificações de segurança
          if (!context || !context.dataset || !value || value <= 0) {
            return '';
          }
          
          // Usar o mapeamento fixo de cor para rótulo
          const backgroundColor = context.dataset.backgroundColor;
          const label = colorToLabel[backgroundColor];
          
          return label || '';
        },
        anchor: 'center',
        align: 'center'
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
        <CalendarTodayIcon />
        Mensal Geral - Santos
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
              onClick={fetchMensalData}
              disabled={loading}
              fullWidth
            >
              {loading ? <CircularProgress size={24} /> : 'Atualizar'}
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* KPIs */}
      {!loading && mensalData.length > 0 && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={3}>
            <KpiCard
              title="Total de Tarefas Mensais"
              value={totalTasks}
              icon={<CalendarTodayIcon />}
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <KpiCard
              title="Tarefas Concluídas"
              value={totalCompleted}
              icon={<CalendarTodayIcon />}
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <KpiCard
              title="Taxa de Conclusão"
              value={`${completionRate}%`}
              icon={<CalendarTodayIcon />}
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <KpiCard
              title="Total de Equipamentos"
              value={totalEquipments}
              icon={<CalendarTodayIcon />}
            />
          </Grid>
        </Grid>
      )}

      {/* Gráfico */}
      {!loading && mensalData.length > 0 && chartData.labels.length > 0 && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Gráfico de Tarefas Mensais por Dia
          </Typography>
          <Box sx={{ height: 400 }}>
            <Bar key="mensal-chart" data={chartData} options={chartOptions} />
          </Box>
        </Paper>
      )}

      {/* Tabela de Contagem por Dia */}
      {!loading && mensalData.length > 0 && (
        <Paper sx={{ mb: 3 }}>
          <Typography variant="h6" sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
            Contagem de Equipamentos Mensais por Dia
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
                {mensalData.map(contract => (
                  <TableRow 
                    key={contract.contractId}
                    sx={{ 
                      backgroundColor: getSectorBackgroundColor(contract.contractName),
                      '&:hover': {
                        backgroundColor: getSectorBackgroundColor(contract.contractName).replace('0.15', '0.25')
                      }
                    }}
                  >
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box 
                          sx={{ 
                            width: 12, 
                            height: 12, 
                            borderRadius: '50%', 
                            backgroundColor: getSectorColor(contract.contractName),
                            flexShrink: 0
                          }} 
                        />
                        <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                          {contract.contractName}
                        </Typography>
                      </Box>
                    </TableCell>
                    {sortedDays.map(day => {
                    const count = dailyStats[contract.contractId]?.[day] || 0;
                    const dayKey = `${contract.contractId}-${day}`;
                    const tasksForDay = tasksByDay[dayKey] || [];
                    
                    return (
                      <TableCell key={day} align="center">
                        {count > 0 ? (
                          <Tooltip 
                            title={`${count} equipamento${count > 1 ? 's' : ''} - Clique para ver detalhes`}
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
                      <strong>{contract.totalEquipments || 0}</strong>
                    </TableCell>
                  </TableRow>
                ))}
                {/* Linha de Total do Dia */}
                <TableRow sx={{ backgroundColor: 'action.hover', fontWeight: 'bold' }}>
                  <TableCell><strong>TOTAL DO DIA</strong></TableCell>
                  {sortedDays.map(day => {
                    const dayTotal = mensalData.reduce((sum, contract) => {
                      return sum + (dailyStats[contract.contractId]?.[day] || 0);
                    }, 0);
                    return (
                      <TableCell key={day} align="center">
                        <strong>{dayTotal}</strong>
                      </TableCell>
                    );
                  })}
                  <TableCell align="center">
                    <strong>
                      {mensalData.reduce((sum, contract) => sum + (contract.totalEquipments || 0), 0)}
                    </strong>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* Popover para detalhes das tarefas */}
      <Popover
        open={popoverState.open}
        anchorEl={popoverState.anchorEl}
        onClose={() => setPopoverState({ open: false, anchorEl: null, tasks: [] })}
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
            Detalhes das Tarefas
          </Typography>
          <List>
            {popoverState.tasks.map((task, index) => (
              <ListItem key={index} sx={{ px: 0 }}>
                <ListItemText
                  primary={task.schoolName}
                  secondary={
                    <Box>
                      <Typography variant="body2">
                        {task.orientation || 'Tarefa'}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                        <Chip 
                          size="small"
                          label={[5, 6].includes(task.taskStatus) ? 'Concluída' : 'Pendente'}
                          color={[5, 6].includes(task.taskStatus) ? 'success' : 'default'}
                        />
                        <IconButton 
                          size="small" 
                          component="a" 
                          href={`https://app.auvo.com.br/task/${task.taskID}`} 
                          target="_blank"
                          title="Abrir no Auvo"
                        >
                          <LinkIcon fontSize="small" />
                        </IconButton>
                      </Box>
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        </Box>
      </Popover>
    </Box>
  );
}
