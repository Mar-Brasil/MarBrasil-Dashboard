import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  TextField,
  Button,
  Alert
} from '@mui/material';

const BillingAdmin = () => {
  const [contracts, setContracts] = useState([]);
  const [billableTaskTypes, setBillableTaskTypes] = useState([]);
  const [selectedContract, setSelectedContract] = useState('');
  const [rates, setRates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingRates, setLoadingRates] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const [contractsRes, taskTypesRes] = await Promise.all([
          fetch('http://127.0.0.1:8000/api/contracts'),
          fetch('http://127.0.0.1:8000/api/billing/task-types')
        ]);

        if (!contractsRes.ok) throw new Error('Erro ao buscar contratos');
        if (!taskTypesRes.ok) throw new Error('Erro ao buscar tipos de tarefa para faturamento');

        const contractsData = await contractsRes.json();
        const taskTypesData = await taskTypesRes.json();

        setContracts(contractsData);
        setBillableTaskTypes(taskTypesData);

      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchInitialData();
  }, []);

  const fetchRates = useCallback(async (contractId) => {
    if (!contractId || billableTaskTypes.length === 0) {
      setRates([]);
      return;
    }

    const selectedContractObject = contracts.find(c => c.id === contractId);
    if (!selectedContractObject) return;

    const contractName = selectedContractObject.name || '';
    const contractPrefix = contractName.split(' - ')[0];

    const filteredTaskTypes = billableTaskTypes.filter(taskType => 
      taskType.description.startsWith(`# ${contractPrefix}`)
    );

    setLoadingRates(true);
    setError(null);
    setSuccess(null);
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/billing/rates/${contractId}`);
      if (!response.ok) throw new Error('Erro ao buscar as taxas do contrato.');
      const fetchedRates = await response.json();
      
      const ratesMap = new Map(fetchedRates.map(rate => [rate.description, rate]));
      
      const combinedRates = filteredTaskTypes.map(taskType => {
        if (ratesMap.has(taskType.description)) {
          return ratesMap.get(taskType.description);
        } else {
          return {
            contract_id: contractId,
            description: taskType.description,
            unit_price: 0,
            additional_price: 0,
          };
        }
      });

      setRates(combinedRates);
    } catch (err) {
      setError(err.message);
      setRates([]);
    } finally {
      setLoadingRates(false);
    }
  }, [billableTaskTypes, contracts]);

  useEffect(() => {
    fetchRates(selectedContract);
  }, [selectedContract, fetchRates]);

  const handleRateChange = (index, field, value) => {
    const newRates = [...rates];
    newRates[index][field] = value;
    setRates(newRates);
  };

  const handleSaveChanges = async () => {
    setError(null);
    setSuccess(null);
    try {
      const promises = rates.map(rate => 
        fetch('http://127.0.0.1:8000/api/billing/rates', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ...rate,
            unit_price: parseFloat(rate.unit_price) || 0,
            additional_price: parseFloat(rate.additional_price) || 0,
          }),
        })
      );
      
      const responses = await Promise.all(promises);
      responses.forEach(res => {
        if (!res.ok) throw new Error('Ocorreu um erro ao salvar uma ou mais taxas.');
      });

      setSuccess('Taxas salvas com sucesso!');
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>Painel Administrativo de Faturamento</Typography>
      
      {loading ? <CircularProgress /> : (
        <FormControl fullWidth sx={{ mb: 3, maxWidth: 500 }}>
          <InputLabel>Selecione um Contrato</InputLabel>
          <Select value={selectedContract} label="Selecione um Contrato" onChange={(e) => setSelectedContract(e.target.value)}>
            {contracts.map((contract) => (
              <MenuItem key={contract.id} value={contract.id}>{contract.name}</MenuItem>
            ))}
          </Select>
        </FormControl>
      )}

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

      {loadingRates ? <CircularProgress /> : selectedContract && rates.length > 0 && (
        <>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Descrição do Serviço</TableCell>
                  <TableCell align="right">Preço Unitário (R$)</TableCell>
                  <TableCell align="right">Preço Adicional (R$)</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {rates.map((rate, index) => (
                  <TableRow key={rate.description}>
                    <TableCell component="th" scope="row">{rate.description}</TableCell>
                    <TableCell align="right">
                      <TextField
                        type="number"
                        variant="outlined"
                        size="small"
                        value={rate.unit_price}
                        onChange={(e) => handleRateChange(index, 'unit_price', e.target.value)}
                        sx={{ width: 120 }}
                      />
                    </TableCell>
                    <TableCell align="right">
                      <TextField
                        type="number"
                        variant="outlined"
                        size="small"
                        value={rate.additional_price}
                        onChange={(e) => handleRateChange(index, 'additional_price', e.target.value)}
                        sx={{ width: 120 }}
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
            <Button variant="contained" color="primary" onClick={handleSaveChanges}>
              Salvar Alterações
            </Button>
          </Box>
        </>
      )}
    </Box>
  );
};

export default BillingAdmin;
