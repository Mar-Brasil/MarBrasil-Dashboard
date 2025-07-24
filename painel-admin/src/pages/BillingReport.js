import React, { useState, useEffect } from 'react';
import {
  Box, Paper, Typography, TextField,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, LinearProgress, CircularProgress,
  Collapse, IconButton, Alert, ListItemText
} from '@mui/material';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import dayjs from 'dayjs';
import axios from 'axios';

function ContractSummary({ data, loading, error }) {
  const [openWithoutService, setOpenWithoutService] = useState(false);
  const [openWithService, setOpenWithService] = useState(false);
  const [expandedSchools, setExpandedSchools] = useState({});

  if (loading) {
    return (
      <Paper sx={{ p: { xs: 1, sm: 2 }, mb: 3, textAlign: 'center', maxWidth: '100%', overflow: 'hidden' }}>
        <CircularProgress size={24} />
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Carregando resumo do contrato...
        </Typography>
      </Paper>
    );
  }

  if (error) {
    return (
      <Paper sx={{ p: { xs: 1, sm: 2 }, mb: 3, maxWidth: '100%', overflow: 'hidden' }}>
        <Alert severity="warning">Não foi possível carregar o resumo do contrato: {error}</Alert>
      </Paper>
    );
  }

  if (!data) {
    return null; // Don't render if data hasn't arrived yet (and not in an error state)
  }

  const { total_equipments, equipments_without_service, equipments_with_service, schools_grouped } = data;
  const hasItemsWithoutService = equipments_without_service?.length > 0;
  const hasItemsWithService = equipments_with_service?.length > 0;

  const toggleSchool = (schoolName) => {
    setExpandedSchools(prev => ({
      ...prev,
      [schoolName]: !prev[schoolName]
    }));
  };

  return (
    <Paper sx={{ p: { xs: 1, sm: 2 }, mb: 3, maxWidth: '100%', overflow: 'hidden' }}>
      <Typography variant="h6" gutterBottom align="center">Resumo do Contrato</Typography>
      <Box sx={{ 
        display: 'flex', 
        flexDirection: { xs: 'column', sm: 'row' },
        justifyContent: 'space-around', 
        alignItems: 'center',
        textAlign: 'center', 
        mb: 2,
        gap: 2
      }}>
        <Box sx={{ width: { xs: '100%', sm: 'auto' } }}>
          <Typography variant="h5">{total_equipments}</Typography>
          <Typography variant="body2" color="text.secondary">Equipamentos Totais</Typography>
        </Box>
        <Box sx={{ width: { xs: '100%', sm: 'auto' } }}>
          <Typography variant="h5" color={hasItemsWithoutService ? 'error' : 'inherit'}>
            {equipments_without_service?.length || 0}
          </Typography>
          <Typography variant="body2" color="text.secondary">Equipamentos Sem Serviço</Typography>
        </Box>
        <Box sx={{ width: { xs: '100%', sm: 'auto' } }}>
          <Typography variant="h5" color="success.main">
            {equipments_with_service?.length || 0}
          </Typography>
          <Typography variant="body2" color="text.secondary">Equipamentos Com Serviço</Typography>
        </Box>
      </Box>
      
      {/* Barra de Progresso */}
      <Box sx={{ mt: 2, mb: 3, px: { xs: 1, sm: 2 }, maxWidth: '100%' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="body2">Progresso da Manutenção</Typography>
          <Typography variant="body2" fontWeight="bold">
            {total_equipments > 0 ? Math.round((equipments_with_service?.length || 0) / total_equipments * 100) : 0}%
          </Typography>
        </Box>
        <LinearProgress 
          variant="determinate" 
          value={total_equipments > 0 ? (equipments_with_service?.length || 0) / total_equipments * 100 : 0} 
          sx={{ 
            height: 10, 
            borderRadius: 5,
            backgroundColor: '#ffebee',
            '& .MuiLinearProgress-bar': {
              backgroundColor: '#4caf50',
              borderRadius: 5
            }
          }}
        />
      </Box>

      {/* Equipamentos com Manutenção */}
      {hasItemsWithService && (
        <React.Fragment>
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            cursor: 'pointer', 
            mt: 2, 
            justifyContent: 'center', 
            bgcolor: '#e8f5e9', 
            p: { xs: 1, sm: 1.5 }, 
            borderRadius: 1,
            maxWidth: '100%',
            overflow: 'hidden'
          }} 
               onClick={() => setOpenWithService(!openWithService)}>
            <IconButton size="small">
              {openWithService ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
            </IconButton>
            <Typography variant="button" sx={{ color: 'success.main', fontWeight: 'bold', textAlign: 'center', width: '100%' }}>
              Equipamentos com Manutenção ({equipments_with_service.length})
            </Typography>
          </Box>
          <Collapse in={openWithService} timeout="auto" unmountOnExit>
            <Box sx={{ mt: 2, maxHeight: 400, overflow: 'auto', maxWidth: '100%' }}>
              {schools_grouped?.map(school => (
                school.with_service.length > 0 && (
                  <Paper key={school.name} variant="outlined" sx={{ mb: 1, overflow: 'hidden' }}>
                    <Box sx={{ 
                      p: { xs: 1, sm: 1.5 }, 
                      bgcolor: '#f5f5f5', 
                      display: 'flex', 
                      alignItems: 'center', 
                      cursor: 'pointer',
                      overflow: 'hidden'
                    }}
                         onClick={() => toggleSchool(`with_${school.name}`)}>
                      <IconButton size="small">
                        {expandedSchools[`with_${school.name}`] ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
                      </IconButton>
                      <Typography 
                        variant="subtitle1" 
                        sx={{ 
                          overflow: 'hidden', 
                          textOverflow: 'ellipsis', 
                          whiteSpace: 'nowrap',
                          width: '100%'
                        }}
                      >
                        {school.name.replace(/\[\d+(?:,\s*\d+)*\]\s*-\s*/, '')} ({school.with_service.length})
                      </Typography>
                    </Box>
                    <Collapse in={expandedSchools[`with_${school.name}`]} timeout="auto" unmountOnExit>
                      <Box sx={{ p: 1 }}>
                        {school.with_service.map(equip => (
                          <Box key={equip.id} sx={{ p: 0.5, borderBottom: '1px solid #eee', overflow: 'hidden' }}>
                            <Typography 
                              variant="body2" 
                              sx={{ 
                                overflow: 'hidden', 
                                textOverflow: 'ellipsis', 
                                whiteSpace: 'nowrap' 
                              }}
                            >
                              {equip.name}
                            </Typography>
                          </Box>
                        ))}
                      </Box>
                    </Collapse>
                  </Paper>
                )
              ))}
            </Box>
          </Collapse>
        </React.Fragment>
      )}

      {/* Equipamentos sem Manutenção */}
      {hasItemsWithoutService && (
        <React.Fragment>
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            cursor: 'pointer', 
            mt: 2, 
            justifyContent: 'center', 
            bgcolor: '#ffebee', 
            p: { xs: 1, sm: 1.5 }, 
            borderRadius: 1,
            maxWidth: '100%',
            overflow: 'hidden'
          }} 
               onClick={() => setOpenWithoutService(!openWithoutService)}>
            <IconButton size="small">
              {openWithoutService ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
            </IconButton>
            <Typography variant="button" sx={{ color: 'error.main', fontWeight: 'bold', textAlign: 'center', width: '100%' }}>
              Equipamentos sem Manutenção ({equipments_without_service.length})
            </Typography>
          </Box>
          <Collapse in={openWithoutService} timeout="auto" unmountOnExit>
            <Box sx={{ mt: 2, maxHeight: 400, overflow: 'auto', maxWidth: '100%' }}>
              {schools_grouped?.map(school => (
                school.without_service.length > 0 && (
                  <Paper key={`without_${school.name}`} variant="outlined" sx={{ mb: 1, overflow: 'hidden' }}>
                    <Box sx={{ 
                      p: { xs: 1, sm: 1.5 }, 
                      bgcolor: '#f5f5f5', 
                      display: 'flex', 
                      alignItems: 'center', 
                      cursor: 'pointer',
                      overflow: 'hidden'
                    }}
                         onClick={() => toggleSchool(`without_${school.name}`)}>
                      <IconButton size="small">
                        {expandedSchools[`without_${school.name}`] ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
                      </IconButton>
                      <Typography 
                        variant="subtitle1" 
                        sx={{ 
                          overflow: 'hidden', 
                          textOverflow: 'ellipsis', 
                          whiteSpace: 'nowrap',
                          width: '100%'
                        }}
                      >
                        {school.name.replace(/\[\d+(?:,\s*\d+)*\]\s*-\s*/, '')} ({school.without_service.length})
                      </Typography>
                    </Box>
                    <Collapse in={expandedSchools[`without_${school.name}`]} timeout="auto" unmountOnExit>
                      <Box sx={{ p: 1 }}>
                        {school.without_service.map(equip => (
                          <Box key={equip.id} sx={{ p: 0.5, borderBottom: '1px solid #eee', overflow: 'hidden' }}>
                            <Typography 
                              variant="body2" 
                              sx={{ 
                                overflow: 'hidden', 
                                textOverflow: 'ellipsis', 
                                whiteSpace: 'nowrap' 
                              }}
                            >
                              {equip.name}
                            </Typography>
                          </Box>
                        ))}
                      </Box>
                    </Collapse>
                  </Paper>
                )
              ))}
            </Box>
          </Collapse>
        </React.Fragment>
      )}
    </Paper>
  );
}

function Row({ row }) {
  const [open, setOpen] = useState(false);

  return (
    <React.Fragment>
      <TableRow sx={{ '& > *': { borderBottom: 'unset' } }}>
        <TableCell>
          <IconButton
            size="small"
            onClick={() => setOpen(!open)}
          >
            {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
          </IconButton>
        </TableCell>
        <TableCell component="th" scope="row" sx={{ 
          maxWidth: { xs: '120px', sm: '200px' },
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap'
        }}>
          {row.user_name}
        </TableCell>
        <TableCell align="center">{row.tasks.length}</TableCell>
        <TableCell>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Box sx={{ width: '100%', mr: 1 }}>
              <LinearProgress 
                variant="determinate" 
                value={row.productivity} 
                sx={{ 
                  height: 10, 
                  borderRadius: 5,
                  backgroundColor: '#f5f5f5',
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: row.productivity < 50 ? '#f44336' : row.productivity < 80 ? '#ff9800' : '#4caf50',
                    borderRadius: 5
                  }
                }}
              />
            </Box>
            <Box sx={{ minWidth: 35 }}>
              <Typography variant="body2" color="text.secondary">{`${Math.round(row.productivity)}%`}</Typography>
            </Box>
          </Box>
        </TableCell>
      </TableRow>
      <TableRow>
        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={4}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Box sx={{ margin: 1, maxWidth: '100%', overflow: 'auto' }}>
              <Typography variant="h6" gutterBottom component="div" align="center">
                Detalhes das Tarefas
              </Typography>
              <Table size="small" aria-label="tasks" sx={{ minWidth: { xs: 300, sm: 500 } }}>
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ width: '50%' }}>Escola</TableCell>
                    <TableCell sx={{ width: '25%' }}>Orientação</TableCell>
                    <TableCell sx={{ width: '25%' }}>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {row.tasks.map((taskDetail, index) => {
                    // Remover os IDs dos equipamentos do início do nome da escola
                    const schoolName = taskDetail.school_name.replace(/\[\d+(?:,\s*\d+)*\]\s*-\s*/, '');
                    
                    return (
                      <TableRow key={`${row.user_name}-task-${index}`}>
                        <TableCell sx={{ 
                          maxWidth: { xs: '150px', sm: '300px' },
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap'
                        }}>
                          {schoolName}
                        </TableCell>
                        <TableCell sx={{ 
                          maxWidth: { xs: '100px', sm: '150px' },
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap'
                        }}>
                          {taskDetail.orientation}
                        </TableCell>
                        <TableCell sx={{ 
                          maxWidth: { xs: '80px', sm: '120px' },
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap'
                        }}>
                          {taskDetail.status}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </React.Fragment>
  );
}

export default function BillingReport() {
  const [contracts, setContracts] = useState([]);
  const [selectedContract, setSelectedContract] = useState('');
  const [startDate, setStartDate] = useState(dayjs().startOf('month').format('YYYY-MM-DD'));
  const [endDate, setEndDate] = useState(dayjs().endOf('month').format('YYYY-MM-DD'));

  const [reportData, setReportData] = useState([]);
  const [summaryData, setSummaryData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState({ report: null, summary: null });

  useEffect(() => {
    const fetchContracts = async () => {
      try {
        const response = await axios.get('/api/contracts');
        setContracts(response.data);
        if (response.data.length > 0) {
          setSelectedContract(response.data[0].id);
        } else {
          setLoading(false);
        }
      } catch (err) {
        setError({ report: 'Falha ao carregar contratos.', summary: null });
        setLoading(false);
      }
    };
    fetchContracts();
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      if (!selectedContract || !startDate || !endDate) {
        setReportData([]);
        setSummaryData(null);
        return;
      }
      setLoading(true);
      setError({ report: null, summary: null });

      const reportUrl = `/api/faturamento?group_id=${selectedContract}&start_date=${startDate}&end_date=${endDate}`;
      const summaryUrl = `/api/contract-summary?group_id=${selectedContract}&start_date=${startDate}&end_date=${endDate}`;

      const reportPromise = axios.get(reportUrl);
      const summaryPromise = axios.get(summaryUrl);

      try {
        const [reportResponse, summaryResponse] = await Promise.all([
          reportPromise,
          summaryPromise
        ]);
        setReportData(reportResponse.data);
        setSummaryData(summaryResponse.data);
      } catch (err) {
        console.error("Error fetching data:", err);
        const isReportError = err.config.url === reportUrl;
        if (isReportError) {
            setError(prev => ({ ...prev, report: err.response?.data?.error || 'Erro ao gerar relatório.' }));
            setReportData([]);
        } else {
            setError(prev => ({ ...prev, summary: err.response?.data?.error || 'Erro ao carregar resumo.' }));
            setSummaryData(null);
        }
      }
      setLoading(false);
    };

    if (selectedContract) {
      fetchData();
    } else {
      setLoading(false);
      setReportData([]);
      setSummaryData(null);
    }
  }, [selectedContract, startDate, endDate]);





  return (
    <Box sx={{ p: { xs: 1, sm: 2, md: 3 }, maxWidth: '100%', margin: '0 auto' }}>
      <Typography variant="h4" gutterBottom align="center">Relatório de Faturamento por Colaborador</Typography>
      
      <Paper sx={{ p: { xs: 1, sm: 2 }, mb: 3 }}>


        <Typography variant="h6" gutterBottom align="center"></Typography>
        <Box sx={{ 
          display: 'flex', 
          flexDirection: { xs: 'column', sm: 'row' }, 
          gap: 2, 
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <TextField
            select
            fullWidth
            label="Contrato"
            value={selectedContract}
            onChange={(e) => setSelectedContract(e.target.value)}
            SelectProps={{ native: true }}
            disabled={contracts.length === 0}
            sx={{ maxWidth: { sm: '400px' } }}
          >
            <option value="" disabled>Selecione um Contrato</option>
            {contracts.map((contract) => (
              <option key={contract.id} value={contract.id}>
                {contract.name}
              </option>
            ))}
          </TextField>
          <Box sx={{ 
            display: 'flex', 
            flexDirection: { xs: 'column', sm: 'row' }, 
            gap: 2, 
            width: { xs: '100%', sm: 'auto' } 
          }}>
            <TextField 
              label="Data Inicial" 
              type="date" 
              value={startDate} 
              onChange={(e) => setStartDate(e.target.value)} 
              InputLabelProps={{ shrink: true }} 
              fullWidth 
              sx={{ maxWidth: { sm: '200px' } }}
            />
            <TextField 
              label="Data Final" 
              type="date" 
              value={endDate} 
              onChange={(e) => setEndDate(e.target.value)} 
              InputLabelProps={{ shrink: true }} 
              fullWidth
              sx={{ maxWidth: { sm: '200px' } }}
            />
          </Box>
        </Box>
      </Paper>

      <ContractSummary data={summaryData} loading={loading} error={error.summary} />

      {loading && <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Box>}
      
      {error.report && !loading && <Alert severity="error" sx={{ mb: 2 }}>{error.report}</Alert>}

      {/* Tabela de Detalhes */}
      {reportData.length > 0 && (
        <TableContainer component={Paper} sx={{ mt: 3, maxWidth: '100%', overflow: 'auto' }}>
          <Table aria-label="collapsible table" sx={{ minWidth: { xs: 400, sm: 650 } }}>
            <TableHead>
              <TableRow>
                <TableCell />
                <TableCell>Colaborador</TableCell>
                <TableCell align="center">Tarefas</TableCell>
                <TableCell align="center">Produtividade</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {reportData.map((row) => (
                <Row key={row.user_name} row={row} />
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {!loading && !error.report && reportData.length === 0 && (
        <Typography sx={{ textAlign: 'center', mt: 4 }}>Nenhum dado para exibir. Selecione os filtros para gerar o relatório.</Typography>
      )}
    </Box>
  );
}
