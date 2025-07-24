import React, { useState } from 'react';
import {
  Box, Paper, Typography, LinearProgress, CircularProgress, Alert, List, ListItem, ListItemText, Collapse, IconButton
} from '@mui/material';

function ContractSummary({ data, loading, error }) {
  const [openWithoutService, setOpenWithoutService] = useState(false);
  const [openWithService, setOpenWithService] = useState(false);
  // Se desejar, pode expandir para mostrar detalhes por escola, igual ao BillingReport.js

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
    return null;
  }

  const { total_equipments, equipments_without_service, equipments_with_service } = data;
  const hasItemsWithoutService = equipments_without_service?.length > 0;
  const hasItemsWithService = equipments_with_service?.length > 0;

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
      {/* Equipamentos com e sem manutenção podem ser detalhados aqui, se quiser */}
    </Paper>
  );
}

export default ContractSummary;
