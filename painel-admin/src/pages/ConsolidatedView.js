import React from 'react';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Grid,
  Alert
} from '@mui/material';

// Função para obter a cor de fundo da célula de porcentagem
const getPercentageColor = (percentage) => {
  if (percentage < 25) return '#FFCDD2'; // Red
  if (percentage < 75) return '#FFF9C4'; // Yellow
  return '#C8E6C9'; // Green
};

// Componente para renderizar uma única linha da tabela de resumo do contrato
const SummaryRow = ({ title, data, backgroundColor }) => {

    const kpiData = data || {}; // Garante que data não seja nulo

  const previstoMes = kpiData.total_previsto || 0;
  const realizadoMes = kpiData.total_realizado || 0;
  const percentage = previstoMes > 0 ? Math.round((realizadoMes / previstoMes) * 100) : 0;
  const displayPercentage = Math.min(100, percentage);
  const excedente = Math.max(0, realizadoMes - previstoMes);

  return (
    <TableRow>
      <TableCell sx={{ fontWeight: 'bold', backgroundColor }}>{title}</TableCell>
      <TableCell align="center">{previstoMes}</TableCell>
      <TableCell align="center">{realizadoMes}</TableCell>
      <TableCell align="center" sx={{ backgroundColor: getPercentageColor(percentage), fontWeight: 'bold' }}>
        {`${displayPercentage}%`}
        {excedente > 0 && !title.startsWith('CORRETIVAS') && (
          <span style={{ marginLeft: '8px', fontWeight: 'normal', color: '#d32f2f' }}>
            Excedente {excedente}
          </span>
        )}
      </TableCell>
      <TableCell align="center">{Math.max(0, previstoMes - realizadoMes)}</TableCell>
    </TableRow>
  );
};

// Componente principal da visão consolidada
const ConsolidatedView = ({ data, isLoading }) => {
    if (isLoading) {
    return <Typography>Carregando dados consolidados...</Typography>;
  }

  if (!data || data.length === 0) {
    return <Alert severity="info">Nenhum dado consolidado para exibir.</Alert>;
  }

  return (
    <Box>
      {data.map(({ contract, kpis, total_equipamentos_ativos }) => (
        <Paper key={contract.id} sx={{ mb: 3, overflow: 'hidden' }} variant="outlined">
          <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(224, 224, 224, 1)' }}>
            <Typography variant="h6" component="h2" sx={{ fontWeight: 'bold' }}>
              SETOR: {contract.name}
            </Typography>
            <Typography variant="body1">
              <strong>TOTAL DE EQUIPAMENTOS ATIVOS:</strong> {total_equipamentos_ativos || 0}
            </Typography>
          </Box>
          <TableContainer>
            <Table size="small" sx={{ tableLayout: 'fixed' }}>
              <TableHead>
                <TableRow sx={{ '& th': { fontWeight: 'bold' } }}>
                  <TableCell width="40%">DESCRIÇÃO</TableCell>
                  <TableCell align="center" width="15%">QTDE. PREV. MÊS</TableCell>
                  <TableCell align="center" width="15%">QTDE. REALIZ. MÊS</TableCell>
                  <TableCell align="center" width="15%">% CONCLUÍDAS</TableCell>
                  <TableCell align="center" width="15%">FALTAM FINALIZAR</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {kpis ? (
                  <>
                    <SummaryRow title={`PREVENTIVA MENSAL - ${contract.name}`} data={kpis.preventiva_mensal} backgroundColor="#FFFF99" />
                    <SummaryRow title={`PREVENTIVA SEMESTRAL - ${contract.name}`} data={kpis.preventiva_semestral} backgroundColor="#FFCC99" />
                    <SummaryRow title={`CORRETIVAS - ${contract.name}`} data={kpis.corretiva} backgroundColor="#99FFCC" />
                  </>
                ) : (
                  <TableRow>
                    <TableCell colSpan={5} align="center">Não há dados de KPI para este contrato.</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      ))}
    </Box>
  );
};

export default ConsolidatedView;
