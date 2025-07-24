import React, { useState, useEffect, useMemo } from 'react';
import {
  Box, Paper, Typography, Alert, LinearProgress
} from '@mui/material';
import axios from 'axios';

// Componentes
import SchoolRow from '../components/dashboard/SchoolRow';
import KpiCard from '../components/dashboard/KpiCard';
import StatusChip from '../components/dashboard/StatusChip';
import ContractsProgressDialog from '../components/dashboard/ContractsProgressDialog';
import ExcedenteDialog from '../components/dashboard/ExcedenteDialog';
import DashboardHeader from '../components/dashboard/DashboardHeader';
import DashboardFilters from '../components/dashboard/DashboardFilters';
import CustomKpiCards from '../components/dashboard/CustomKpiCards';

// Utilitários
import { isInPeriod } from '../utils/dateUtils';
import {
  getExcedentEquipments,
  computeCustomKpis,
  cleanSchoolName,
} from '../utils/dashboardUtils';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

const Dashboard = () => {
  // Estado para os filtros
  const [selectedContract, setSelectedContract] = useState('all');
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth());
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [searchTerm, setSearchTerm] = useState('');
  const [showOnlyActive, setShowOnlyActive] = useState(true);

  // Estado para dados carregados da API
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [schools, setSchools] = useState([]);
  const [contracts, setContracts] = useState([]);
  const [taskTypeMap, setTaskTypeMap] = useState({});

  // Estado para diálogos
  const [contractsProgressDialog, setContractsProgressDialog] = useState({
    open: false,
    loading: false,
    contracts: [],
  });
  const [excedenteDialog, setExcedenteDialog] = useState({
    open: false,
    title: '',
    items: [],
  });

  // Calcula o intervalo de datas baseado no mês/ano selecionados
  const dateRange = useMemo(() => {
    const startDate = new Date(selectedYear, selectedMonth, 1);
    const endDate = new Date(selectedYear, selectedMonth + 1, 0); // Último dia do mês
    return {
      start: startDate.toISOString(),
      end: endDate.toISOString(),
    };
  }, [selectedMonth, selectedYear]);

  // Informações do contrato selecionado
  const selectedContractInfo = useMemo(() => {
    if (selectedContract === 'all') {
      return { id: 'all', name: 'Todos os Contratos' };
    }
    const contract = contracts.find(c => c.id === selectedContract);
    return contract || { id: 'all', name: 'Contrato não encontrado' };
  }, [selectedContract, contracts]);

  // Filtra escolas com base nos critérios atuais
  const filteredSchools = useMemo(() => {
    if (!schools.length) return [];
    
    let filtered = schools;
    
    // Filtro por contrato
    if (selectedContract !== 'all') {
      filtered = filtered.filter(school => 
        school.contract_id === selectedContract
      );
    }
    
    // Filtro por nome da escola
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      filtered = filtered.filter(school => 
        school.school_info?.name?.toLowerCase().includes(searchLower) ||
        school.school_info?.description?.toLowerCase().includes(searchLower)
      );
    }
    
    // Filtro por escolas com equipamentos
    if (showOnlyActive) {
      filtered = filtered.filter(school => {
        const activeEquipCount = (school.equipments || []).filter(equip => 
          equip.active !== false && equip.active !== 0
        ).length;
        return activeEquipCount > 0;
      });
    }
    
    return filtered;
  }, [schools, selectedContract, searchTerm, showOnlyActive]);
  
  // Calcula KPIs para as escolas filtradas
  const customKpis = useMemo(() => {
    if (loading || filteredSchools.length === 0) {
      return {
        mensalPct: 0,
        semestralPct: 0,
        pmocPct: 0,
        corretivaCount: 0,
      };
    }
    return computeCustomKpis(filteredSchools, dateRange.start, dateRange.end);
  }, [filteredSchools, dateRange, loading]);

  // Calcula equipamentos excedentes para cada categoria
  const mensalExItems = useMemo(() => {
    return getExcedentEquipments(
      filteredSchools,
      { keywords: ['mensal', 'preventiva mensal'] },
      478, // Denominador para mensais
      dateRange.start,
      dateRange.end
    );
  }, [filteredSchools, dateRange]);

  const semestralExItems = useMemo(() => {
    return getExcedentEquipments(
      filteredSchools,
      { keywords: ['semestral', 'preventiva semestral'] },
      80, // Denominador para semestrais
      dateRange.start,
      dateRange.end
    );
  }, [filteredSchools, dateRange]);

  const pmocExItems = useMemo(() => {
    return getExcedentEquipments(
      filteredSchools,
      { keywords: ['pmoc'] },
      478, // Denominador para PMOC
      dateRange.start,
      dateRange.end
    );
  }, [filteredSchools, dateRange]);

  // Diálogos de abertura/fechamento
  const openExDialog = (title, items) => {
    setExcedenteDialog({
      open: true,
      title,
      items,
    });
  };

  const closeExDialog = () => {
    setExcedenteDialog(prev => ({ ...prev, open: false }));
  };

  const openContractsProgressDialog = async () => {
    setContractsProgressDialog(prev => ({ ...prev, open: true, loading: true }));
    try {
      const response = await axios.get(`${API_BASE_URL}/contract-progress`);
      setContractsProgressDialog(prev => ({ 
        ...prev, 
        contracts: response.data, 
        loading: false 
      }));
    } catch (error) {
      console.error('Erro ao carregar progresso dos contratos:', error);
      setContractsProgressDialog(prev => ({ 
        ...prev, 
        contracts: [], 
        loading: false 
      }));
    }
  };

  const closeContractsProgressDialog = () => {
    setContractsProgressDialog(prev => ({ ...prev, open: false }));
  };

  // Carrega dados iniciais da API
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const [schoolsResponse, contractsResponse, taskTypesResponse] = await Promise.all([
          axios.get(`${API_BASE_URL}/schools`),
          axios.get(`${API_BASE_URL}/contracts`),
          axios.get(`${API_BASE_URL}/task-types`)
        ]);
        
        setSchools(schoolsResponse.data);
        setContracts(contractsResponse.data);
        
        // Processa tipos de tarefas em um mapa para fácil acesso
        const typeMap = {};
        taskTypesResponse.data.forEach(type => {
          typeMap[type.id] = type;
        });
        setTaskTypeMap(typeMap);
        
      } catch (err) {
        console.error('Erro ao carregar dados iniciais:', err);
        setError('Falha ao carregar dados. Tente novamente mais tarde.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);

  // Renderiza estados de loading e erro
  if (loading) {
    return (
      <Box sx={{ width: '100%', mt: 4, textAlign: 'center' }}>
        <LinearProgress />
        <Typography variant="body1" sx={{ mt: 2 }}>
          Carregando dados do dashboard...
        </Typography>
      </Box>
    );
  }
  
  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 4 }}>
        {error}
      </Alert>
    );
  }

  // Render principal do dashboard
  return (
    <Box sx={{ p: 3 }}>
      {/* Cabeçalho do Dashboard */}
      <DashboardHeader 
        schools={filteredSchools}
        selectedContractInfo={selectedContractInfo}
        openContractsProgressDialog={openContractsProgressDialog}
        contractsProgressDialog={contractsProgressDialog}
        dateRange={dateRange}
      />

      {/* Filtros */}
      <DashboardFilters
        selectedContract={selectedContract}
        setSelectedContract={setSelectedContract}
        selectedMonth={selectedMonth}
        setSelectedMonth={setSelectedMonth}
        selectedYear={selectedYear}
        setSelectedYear={setSelectedYear}
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        showOnlyActive={showOnlyActive}
        setShowOnlyActive={setShowOnlyActive}
        contracts={contracts}
      />

      {/* KPIs específicos (Mensal, Semestral, PMOC, Corretiva) */}
      <CustomKpiCards 
        kpiData={customKpis}
        openExDialog={openExDialog}
        mensalItems={mensalExItems}
        semestralItems={semestralExItems}
        pmocItems={pmocExItems}
      />

      {/* Lista de escolas com acordeões */}
      <Paper variant="outlined" sx={{ p: 2 }}>
        {filteredSchools.length === 0 ? (
          <Typography variant="body1" align="center" sx={{ py: 3 }}>
            Nenhuma escola encontrada com os filtros selecionados.
          </Typography>
        ) : (
          filteredSchools.map(school => (
            <SchoolRow
              key={school.id}
              school={school}
              taskTypeMap={taskTypeMap}
              selectedContractInfo={selectedContractInfo}
              dateRange={dateRange}
            />
          ))
        )}
      </Paper>

      {/* Diálogos */}
      <ContractsProgressDialog
        open={contractsProgressDialog.open}
        contracts={contractsProgressDialog.contracts}
        loading={contractsProgressDialog.loading}
        onClose={closeContractsProgressDialog}
      />

      <ExcedenteDialog
        open={excedenteDialog.open}
        title={excedenteDialog.title}
        items={excedenteDialog.items}
        onClose={closeExDialog}
      />
    </Box>
  );
};

export default Dashboard;
