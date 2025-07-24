import React, { useEffect, useState } from 'react';
import {
  Box, Typography, Grid, Paper, FormControl, InputLabel, Select, MenuItem, IconButton, Button,
  TextField, CircularProgress, Alert, TableContainer, Table, TableHead, TableRow, TableCell, TableBody,
} from '@mui/material';
import axios from 'axios';
import CalendarViewWeekIcon from '@mui/icons-material/CalendarViewWeek';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import * as XLSX from 'xlsx';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

const TASK_TYPE_IDS = {
  PREVENTIVA_SEMESTRAL: 175652,
};

const KPI_CATEGORIES = {
  SEMESTRAL: {
    ids: [TASK_TYPE_IDS.PREVENTIVA_SEMESTRAL],
    keywords: ['semestral', 'preventiva semestral'],
  },
};

const matchesCategory = (task) => {
  const orientation = (task.orientation || '').toLowerCase();
  const matchId = KPI_CATEGORIES.SEMESTRAL.ids.includes(task.taskType);
  const matchKeyword = KPI_CATEGORIES.SEMESTRAL.keywords.some(k => orientation.includes(k));
  return matchId || matchKeyword;
};

// Parse equipmentsId field in various formats -> array of ids (string/number)
const parseEquipIds = (raw) => {
  if (!raw) return [];
  if (Array.isArray(raw)) return raw;
  if (typeof raw === 'string') {
    const trimmed = raw.trim();
    if (trimmed.startsWith('[')) {
      try {
        const parsed = JSON.parse(trimmed);
        return Array.isArray(parsed) ? parsed : [];
      } catch (_) {
        return trimmed.match(/\d+/g) || [];
      }
    }
    return trimmed.split(',').map(t => t.trim()).filter(Boolean);
  }
  return [];
};

const isInPeriod = (dateLike, start, end) => {
  const d = new Date(dateLike);
  if (isNaN(d)) return false;
  return d >= new Date(start) && d <= new Date(end);
};

export default function SemestralPlanner() {
  const today = new Date();
  const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
  const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);

  const [contracts, setContracts] = useState([]);
  const [selectedContract, setSelectedContract] = useState('');
  const [dateRange, setDateRange] = useState({
    start: firstDay.toISOString().slice(0, 10),
    end: lastDay.toISOString().slice(0, 10),
  });
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch contracts on mount
  useEffect(() => {
    const fetchContracts = async () => {
      try {
        const res = await axios.get(`${API_BASE_URL}/contracts`);
        setContracts(res.data || []);
        if (res.data && res.data.length > 0) setSelectedContract(String(res.data[0].id));
      } catch (e) {
        console.error(e);
        setError('Falha ao buscar contratos');
      }
    };
    fetchContracts();
  }, []);

  // Fetch dashboard-like data for selected contract & period
  useEffect(() => {
    if (!selectedContract) return;
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const params = { start_date: dateRange.start, end_date: dateRange.end };
        const res = await axios.get(`${API_BASE_URL}/dashboard/${selectedContract}`, { params });
        setData(res.data);
      } catch (e) {
        console.error(e);
        setError('Falha ao buscar dados');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [selectedContract, dateRange]);

  // Compute equipments without semestral task
  const [expanded, setExpanded] = useState(null);

  const missingBySchool = React.useMemo(() => {
    if (!data || !data.schools) return [];
    const result = [];
    data.schools.forEach((school) => {
      const allEquip = (school.equipments || []).filter(eq => {
        const activeVal = eq.active !== undefined ? eq.active : eq.ativo;
        return activeVal === 1 || activeVal === true || activeVal === '1' || activeVal === 'Sim';
      });
      const semestralTasks = (school.tasks || []).filter(t => t.taskUrl && matchesCategory(t) && isInPeriod(t.checkInDate || t.lastUpdate, dateRange.start, dateRange.end));
      const doneEquipIds = new Set();
      semestralTasks.forEach(t => parseEquipIds(t.equipmentsId).forEach(id => doneEquipIds.add(String(id))));
      const missingEquip = allEquip.filter(eq => !doneEquipIds.has(String(eq.id)));
      if (missingEquip.length > 0) {
        result.push({
          school: school.school_info?.description || 'Escola',
          missing: missingEquip,
        });
      }
    });
    return result;
  }, [data, dateRange]);

  const handleExport = () => {
    const rows = [];
    missingBySchool.forEach(row => {
      row.missing.forEach(eq => {
        rows.push({
          Escola: row.school,
          Equipamento: eq.name || eq.description || `ID ${eq.id}`
        });
      });
    });
    const ws = XLSX.utils.json_to_sheet(rows);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Pendentes');
    XLSX.writeFile(wb, `pendentes_semestral_${selectedContract}_${dateRange.start}_${dateRange.end}.xlsx`);
  };

  const renderEquipList = (equipArr) => (
    <Box sx={{ pl: 4 }}>
      <ul style={{ margin: 0 }}>
        {equipArr.map(eq => (
          <li key={eq.id || eq.name}>{eq.name || eq.description || `ID ${eq.id}`}</li>
        ))}
      </ul>
    </Box>
  );

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <CalendarViewWeekIcon color="info" /> Maquinas sem Preventiva Semestral
      </Typography>

      {/* Filters */}
      <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={4} md={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Contrato</InputLabel>
              <Select value={selectedContract} label="Contrato" onChange={e => setSelectedContract(e.target.value)}>
                {contracts.map(c => (
                <MenuItem key={c.id} value={String(c.id)}>
                  {c.description || c.name || c.contract_name || `Contrato ${c.id}`}
                </MenuItem>
              ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={6} sm={4} md={2}>
            <TextField label="Data Início" type="date" size="small" fullWidth value={dateRange.start} onChange={e => setDateRange(r => ({ ...r, start: e.target.value }))} InputLabelProps={{ shrink: true }} />
          </Grid>
          <Grid item xs={6} sm={4} md={2}>
            <TextField label="Data Final" type="date" size="small" fullWidth value={dateRange.end} onChange={e => setDateRange(r => ({ ...r, end: e.target.value }))} InputLabelProps={{ shrink: true }} />
          </Grid>
            <Grid item xs={12} sm={4} md={2}>
            <Button fullWidth variant="contained" size="small" onClick={handleExport} disabled={missingBySchool.length===0}>
              Exportar Excel
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {loading && <CircularProgress />}
      {error && <Alert severity="error">{error}</Alert>}

      {!loading && !error && (
        <TableContainer component={Paper} variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Escola</TableCell>
                <TableCell align="right">Equipamentos sem Semestral</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {missingBySchool.length === 0 && (
                <TableRow><TableCell colSpan={2}>Nenhuma pendência encontrada neste período.</TableCell></TableRow>
              )}
              {missingBySchool.map((row, idx) => (
                <React.Fragment key={idx}>
                  <TableRow>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <IconButton size="small" onClick={() => setExpanded(expanded === idx ? null : idx)}>
                          {expanded === idx ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
                        </IconButton>
                        {row.school}
                      </Box>
                    </TableCell>
                    <TableCell align="right">{row.missing.length}</TableCell>
                  </TableRow>
                  {expanded === idx && (
                    <TableRow>
                      <TableCell colSpan={2}>{renderEquipList(row.missing)}</TableCell>
                    </TableRow>
                  )}
                </React.Fragment>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}
