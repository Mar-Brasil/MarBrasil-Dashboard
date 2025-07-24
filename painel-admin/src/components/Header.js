import React from 'react';
import {
  Box, Typography, FormControl, InputLabel, Select, MenuItem, TextField
} from '@mui/material';

// Recebe as props necessárias do Dashboard
const Header = ({
  contracts,
  selectedContract,
  onContractChange,
  dateRange,
  onDateChange
}) => (
  <Box sx={{ mb: 2, display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, alignItems: 'center', gap: 2 }}>
    <Typography variant="h5" sx={{ flexGrow: 1 }}>
      Dashboard de Tarefas
    </Typography>
    <FormControl sx={{ minWidth: 200 }}>
      <InputLabel id="contract-select-label">Contrato</InputLabel>
      <Select
        labelId="contract-select-label"
        value={selectedContract}
        label="Contrato"
        onChange={onContractChange}
      >
        {contracts.map(contract => (
          <MenuItem key={contract.id} value={contract.id}>{contract.name}</MenuItem>
        ))}
      </Select>
    </FormControl>
    <TextField
      label="Data Inicial"
      type="date"
      value={dateRange.start}
      onChange={e => onDateChange('start', e.target.value)}
      InputLabelProps={{ shrink: true }}
      sx={{ minWidth: 150 }}
    />
    <TextField
      label="Data Final"
      type="date"
      value={dateRange.end}
      onChange={e => onDateChange('end', e.target.value)}
      InputLabelProps={{ shrink: true }}
      sx={{ minWidth: 150 }}
    />
  </Box>
);

export default Header;