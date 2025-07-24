import React, { useState, useEffect, useCallback } from 'react';
import { 
  Typography, Box, CircularProgress, Alert, Paper, 
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, 
  TextField, MenuItem, FormControl, InputLabel, Select,
  Collapse, IconButton, LinearProgress
} from '@mui/material';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import dayjs from 'dayjs';
import axios from 'axios';
import { format } from 'date-fns';

function FinancialSummary({ data, loading, error }) {
  if (loading) {
    return (
      <Paper sx={{ p: 2, mb: 3, textAlign: 'center' }}>
        <CircularProgress size={24} />
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Carregando resumo financeiro...
        </Typography>
      </Paper>
    );
  }

  if (error) {
    return (
      <Paper sx={{ p: 2, mb: 3 }}>
        <Alert severity="warning">{error}</Alert>
      </Paper>
    );
  }

  if (!data || data.summary.length === 0) {
    return null;
  }

  const formatCurrency = (value) => 
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value || 0);

  return (
    <TableContainer component={Paper} sx={{ mt: 3, maxWidth: '100%', overflow: 'auto' }}>
      <Typography variant="h6" sx={{ p: 2 }}>Resumo Financeiro</Typography>
      <Table aria-label="financial summary table">
        <TableHead>
          <TableRow>
            <TableCell>Descrição</TableCell>
            <TableCell align="center">Executado</TableCell>
            <TableCell align="right">Unitário</TableCell>
            <TableCell align="right">Adicional</TableCell>
            <TableCell align="right">Total</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {data.summary.map((item) => (
            <TableRow key={item.description}>
              <TableCell component="th" scope="row">{item.description}</TableCell>
              <TableCell align="center">{item.executed}</TableCell>
              <TableCell align="right">{formatCurrency(item.unit_price)}</TableCell>
              <TableCell align="right">{formatCurrency(item.additional_price)}</TableCell>
              <TableCell align="right" sx={{ fontWeight: 'bold' }}>{formatCurrency(item.total)}</TableCell>
            </TableRow>
          ))}
          <TableRow>
            <TableCell colSpan={4} align="right" sx={{ fontWeight: 'bold', borderTop: '2px solid #ccc' }}>TOTAL</TableCell>
            <TableCell align="right" sx={{ fontWeight: 'bold', fontSize: '1.1rem', borderTop: '2px solid #ccc' }}>
              {formatCurrency(data.grand_total)}
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  );
}

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
        <Alert severity="warning">{error}</Alert>
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
  const [financialData, setFinancialData] = useState(null);
  
  const [loading, setLoading] = useState({ report: false, summary: false, financial: false });
  const [error, setError] = useState({ report: null, summary: null, financial: null });

  // Boolean derived state to simplify loading checks in the UI
  const isAnyLoading = loading.report || loading.summary || loading.financial;

  const handleFilterChange = useCallback(() => {
    if (selectedContract && startDate && endDate) {
      const contractId = parseInt(selectedContract, 10);
      if (isNaN(contractId)) {
        return;
      }

      // Adiciona um tratamento para evitar que a data seja interpretada como UTC
      const formattedStartDate = format(new Date(startDate + 'T00:00:00'), 'yyyy-MM-dd');
      const formattedEndDate = format(new Date(endDate + 'T00:00:00'), 'yyyy-MM-dd');

      setLoading({ report: true, summary: true, financial: true });
      setError({ report: null, summary: null, financial: null });

      const reportUrl = `http://127.0.0.1:8000/api/billing/report/${contractId}`;
      const summaryUrl = `http://127.0.0.1:8000/api/contracts/${contractId}/summary`;
      const financialUrl = `http://127.0.0.1:8000/api/billing/financial_summary/${contractId}`;

      const params = { start_date: formattedStartDate, end_date: formattedEndDate };

      // Fetch Report Data
      axios.get(reportUrl, { params })
        .then(response => {
          setReportData(response.data.collaborators || []);
        })
        .catch(err => {
          console.error("Erro ao buscar dados do relatório:", err);
          setError(prev => ({ ...prev, report: 'Falha ao carregar dados do relatório.' }));
        })
        .finally(() => {
          setLoading(prev => ({ ...prev, report: false }));
        });

      // Fetch Contract Summary
      axios.get(summaryUrl)
        .then(response => {
          setSummaryData(response.data);
        })
        .catch(err => {
          console.error("Erro ao buscar resumo do contrato:", err);
          setError(prev => ({ ...prev, summary: 'Não foi possível carregar o resumo do contrato.' }));
        })
        .finally(() => {
          setLoading(prev => ({ ...prev, summary: false }));
        });

      // Fetch Financial Summary
      axios.get(financialUrl, { params })
        .then(response => {
          setFinancialData(response.data);
        })
        .catch(err => {
          console.error("Erro ao buscar resumo financeiro:", err);
          setError(prev => ({ ...prev, financial: 'Falha ao carregar resumo financeiro.' }));
        })
        .finally(() => {
          setLoading(prev => ({ ...prev, financial: false }));
        });
    }
  }, [selectedContract, startDate, endDate]);

  useEffect(() => {
    handleFilterChange();
  }, [handleFilterChange]);

  useEffect(() => {
    async function fetchContracts() {
      try {
        const response = await axios.get('http://127.0.0.1:8000/api/contracts');
        const formattedContracts = response.data.map(c => ({ id: c.id, name: c.name }));
        setContracts(formattedContracts);
      } catch (err) {
        console.error("Erro ao buscar contratos:", err);
        setError(prev => ({ ...prev, report: 'Falha ao carregar a lista de contratos.' }));
      }
    }
    fetchContracts();
  }, []);

  return (
    <Box sx={{ p: { xs: 1, sm: 2, md: 3 }, maxWidth: '100%', margin: '0 auto' }}>
      <Typography variant="h4" gutterBottom align="center">Relatório de Faturamento</Typography>
      
      <Paper sx={{ p: { xs: 1, sm: 2 }, mb: 3 }}>
        <Box sx={{ 
          display: 'flex', 
          flexDirection: { xs: 'column', sm: 'row' }, 
          gap: 2, 
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <FormControl fullWidth sx={{ maxWidth: { sm: '400px' } }}>
            <InputLabel id="contract-select-label">Contrato</InputLabel>
            <Select
              labelId="contract-select-label"
              id="contract-select"
              value={selectedContract}
              label="Contrato"
              onChange={(e) => setSelectedContract(e.target.value)}
              disabled={contracts.length === 0 || isAnyLoading}
            >
              <MenuItem value="">
                <em>Selecione um Contrato</em>
              </MenuItem>
              {contracts.map((contract) => (
                <MenuItem key={contract.id} value={contract.id}>
                  {contract.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
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
              disabled={isAnyLoading}
              sx={{ maxWidth: { sm: '200px' } }}
            />
            <TextField 
              label="Data Final" 
              type="date" 
              value={endDate} 
              onChange={(e) => setEndDate(e.target.value)} 
              InputLabelProps={{ shrink: true }} 
              fullWidth
              disabled={isAnyLoading}
              sx={{ maxWidth: { sm: '200px' } }}
            />
          </Box>
        </Box>
      </Paper>

      {isAnyLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {!isAnyLoading && selectedContract && (
        <>
          <ContractSummary data={summaryData} loading={false} error={error.summary} />
          <FinancialSummary data={financialData} loading={false} error={error.financial} />
          
          {error.report && <Alert severity="error" sx={{ mb: 2 }}>{error.report}</Alert>}

          {reportData.length > 0 && (
            <TableContainer component={Paper} sx={{ mt: 3, maxWidth: '100%', overflow: 'auto' }}>
              <Typography variant="h6" sx={{ p: 2 }}>Detalhes por Colaborador</Typography>
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
        </>
      )}

      {!isAnyLoading && !selectedContract && (
        <Typography sx={{ textAlign: 'center', mt: 4 }}>
          Selecione um contrato para começar.
        </Typography>
      )}
    </Box>
  );
}
