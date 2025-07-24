import React, { useState, useEffect, useMemo } from 'react';
import {
  Box, Grid, Typography, Paper, CircularProgress, Alert,
  FormControl, InputLabel, Select, MenuItem, Button, IconButton,
  TextField, Tooltip, Chip, Badge, Divider
} from '@mui/material';
import SchoolIcon from '@mui/icons-material/School';
import PeopleIcon from '@mui/icons-material/People';
import BuildIcon from '@mui/icons-material/Build';
import AssessmentIcon from '@mui/icons-material/Assessment';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import { styled } from '@mui/material/styles';
import axios from 'axios';

// Componentes personalizados
import KpiCard from '../components/dashboard/KpiCard';
import SchoolRow from '../components/dashboard/SchoolRow';
import TasksTable from '../components/dashboard/TasksTable';
import EquipmentTable from '../components/dashboard/EquipmentTable';
import ContractsProgressDialog from '../components/dashboard/ContractsProgressDialog';

// Utilitários
import { formatDate, isInPeriod } from '../utils/dateUtils';
import { 
  specialTaskIconsConfig, 
  getPercentageColor, 
  cleanSchoolName,
  getSchoolPercentual,
  computeCustomKpis
} from '../utils/dashboardUtils';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

// Estilos personalizados
const StyledPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(2),
  marginBottom: theme.spacing(2),
}));

const Dashboard = () => {
  // Estados
  const [dateRange, setDateRange] = useState({
    start: new Date().toISOString().slice(0, 8) + '01', // Primeiro dia do mês atual
    end: new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0).toISOString().slice(0, 10) // Último dia do mês atual
  });
  
  const [contracts, setContracts] = useState([]);
  const [selectedContract, setSelectedContract] = useState('all');
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [contractsProgress, setContractsProgress] = useState({ open: false, loading: false, data: [] });

  // Buscar contratos ao carregar o componente
  useEffect(() => {
    const fetchContracts = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/contracts`);
        const list = response.data || [];
        setContracts([{ id: 'all', name: 'Todos os Contratos' }, ...list]);
      } catch (err) {
        setError('Falha ao carregar contratos');
        console.error('Erro ao buscar contratos:', err);
      }
    };
    
    fetchContracts();
  }, []);

  // Buscar dados do dashboard quando o contrato ou data mudar
  useEffect(() => {
    if (selectedContract) {
      fetchDashboardData();
    }
  }, [selectedContract, dateRange]);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = {
        start_date: dateRange.start,
        end_date: dateRange.end
      };
      
      const url = selectedContract === 'all' 
        ? `${API_BASE_URL}/dashboard` 
        : `${API_BASE_URL}/dashboard/${selectedContract}`;
      
      const response = await axios.get(url, { params });
      setDashboardData(response.data);
    } catch (err) {
      setError('Falha ao carregar dados do dashboard');
      console.error('Erro ao buscar dados do dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  // Calcular métricas para os KPIs
  const metrics = useMemo(() => {
    if (!dashboardData) return null;
    
    const schools = dashboardData.schools || [];
    const tasks = schools.flatMap(school => school.tasks || []);
    const completedTasks = tasks.filter(task => [5, 6].includes(task.taskStatus));
    
    return {
      totalSchools: schools.length,
      totalTasks: tasks.length,
      completedTasks: completedTasks.length,
      completionRate: tasks.length > 0 ? Math.round((completedTasks.length / tasks.length) * 100) : 0,
      ...computeCustomKpis(schools, dateRange.start, dateRange.end)
    };
  }, [dashboardData, dateRange]);

  // Manipuladores de eventos
  const handleContractChange = (event) => {
    setSelectedContract(event.target.value);
  };

  const handleDateChange = (field) => (event) => {
    setDateRange(prev => ({
      ...prev,
      [field]: event.target.value
    }));
  };

  const handleOpenContractsProgress = async () => {
    setContractsProgress(prev => ({ ...prev, open: true, loading: true }));
    
    try {
      const params = {
        start_date: dateRange.start,
        end_date: dateRange.end
      };
      
      const response = await axios.get(`${API_BASE_URL}/dashboard`, { params });
      const progressData = (response.data.schools || []).map(school => ({
        id: school.school_info?.id,
        name: cleanSchoolName(school.school_info?.description || 'Escola sem nome'),
        completed: (school.tasks || []).filter(t => [5, 6].includes(t.taskStatus)).length,
        total: school.tasks?.length || 0,
        pct: getSchoolPercentual(school, dateRange.start, dateRange.end)
      }));
      
      setContractsProgress(prev => ({ ...prev, data: progressData }));
    } catch (err) {
      console.error('Erro ao buscar progresso dos contratos:', err);
    } finally {
      setContractsProgress(prev => ({ ...prev, loading: false }));
    }
  };

  // Renderização condicional
  if (loading && !dashboardData) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ my: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Box sx={{ p: { xs: 1, md: 3 } }}>
      {/* Cabeçalho e Filtros */}
      <StyledPaper>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Contrato</InputLabel>
              <Select
                value={selectedContract}
                onChange={handleContractChange}
                label="Contrato"
              >
                {contracts.map(contract => (
                  <MenuItem key={contract.id} value={contract.id}>
                    {contract.name || contract.description}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} md={8} container spacing={1}>
            <Grid item xs={12} sm={5}>
              <TextField
                fullWidth
                label="Data Inicial"
                type="date"
                size="small"
                value={dateRange.start}
                onChange={handleDateChange('start')}
                InputLabelProps={{
                  shrink: true,
                }}
              />
            </Grid>
            <Grid item xs={12} sm={5}>
              <TextField
                fullWidth
                label="Data Final"
                type="date"
                size="small"
                value={dateRange.end}
                onChange={handleDateChange('end')}
                InputLabelProps={{
                  shrink: true,
                }}
              />
            </Grid>
            <Grid item xs={12} sm={2}>
              <Button 
                fullWidth 
                variant="contained" 
                onClick={fetchDashboardData}
                sx={{ height: '40px' }}
              >
                Aplicar
              </Button>
            </Grid>
          </Grid>
        </Grid>
      </StyledPaper>

      {/* KPIs */}
      {metrics && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <KpiCard
              title="Escolas"
              value={metrics.totalSchools}
              icon={<SchoolIcon color="primary" />}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <KpiCard
              title="Tarefas"
              value={`${metrics.completedTasks}/${metrics.totalTasks}`}
              icon={<AssignmentIcon color="primary" />}
              extra={
                <Chip 
                  label={`${metrics.completionRate}%`} 
                  size="small" 
                  color={metrics.completionRate === 100 ? 'success' : 'default'}
                />
              }
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <KpiCard
              title="Preventivas Mensais"
              value={metrics.mensalPct ? `${metrics.mensalPct}%` : 'N/A'}
              icon={<EventRepeatIcon color="primary" />}
              extra={
                metrics.mensalExcedent > 0 && (
                  <Tooltip title={`${metrics.mensalExcedent} equipamentos excedentes`}>
                    <Badge badgeContent={metrics.mensalExcedent} color="error">
                      <InfoOutlinedIcon color="action" />
                    </Badge>
                  </Tooltip>
                )
              }
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <KpiCard
              title="Preventivas Semestrais"
              value={metrics.semestralPct ? `${metrics.semestralPct}%` : 'N/A'}
              icon={<CalendarViewWeekIcon color="primary" />}
              extra={
                metrics.semestralExcedent > 0 && (
                  <Tooltip title={`${metrics.semestralExcedent} equipamentos excedentes`}>
                    <Badge badgeContent={metrics.semestralExcedent} color="error">
                      <InfoOutlinedIcon color="action" />
                    </Badge>
                  </Tooltip>
                )
              }
            />
          </Grid>
        </Grid>
      )}

      {/* Lista de Escolas */}
      <StyledPaper>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6" component="h2">
            Escolas
          </Typography>
          <Button 
            variant="outlined" 
            startIcon={<AssessmentIcon />}
            onClick={handleOpenContractsProgress}
          >
            Progresso por Contrato
          </Button>
        </Box>
        
        <Divider sx={{ mb: 2 }} />
        
        {dashboardData?.schools?.length > 0 ? (
          dashboardData.schools.map(school => (
            <SchoolRow 
              key={school.school_info?.id} 
              school={school} 
              dateRange={dateRange}
              sx={{ mb: 2 }}
            />
          ))
        ) : (
          <Typography variant="body1" color="textSecondary" align="center" sx={{ py: 4 }}>
            Nenhuma escola encontrada para os filtros selecionados.
          </Typography>
        )}
      </StyledPaper>

      {/* Diálogo de Progresso de Contratos */}
      <ContractsProgressDialog
        open={contractsProgress.open}
        loading={contractsProgress.loading}
        data={contractsProgress.data}
        onClose={() => setContractsProgress(prev => ({ ...prev, open: false }))}
      />
    </Box>
  );
};

export default Dashboard;
