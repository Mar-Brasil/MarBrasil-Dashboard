import React from 'react';
import {
  Box,
  Typography,
  TableContainer,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  Paper,
  LinearProgress
} from '@mui/material';

// Função para obter os dados reais de contratos quando disponíveis
const getContractRealData = (contractId, contractData) => {
  // Procura o contrato nos dados de progresso
  const contract = contractData.find(c => c.id === contractId);
  if (!contract) return null;
  
  // Extrai métricas do contrato
  const totalEquipments = contract.total_equipments || contract.total || 0;
  const mensalTotal = totalEquipments;
  const semestralTotal = Math.round(totalEquipments / 6); // Estimativa: 1/6 do total para semestral
  
  // Calcula valores para tarefas mensais
  const mensalPrevisto = contract.mensal_previsto || mensalTotal || 0;
  const mensalRealizado = contract.mensal_realizado || contract.completed || 0;
  const mensalConcluido = contract.mensal_pct || contract.pct || 0;
  const mensalFaltam = Math.max(0, mensalPrevisto - mensalRealizado);
  const mensalDias = Math.ceil(mensalFaltam / 20) || 1; // Estimativa de 20 tarefas por dia
  
  // Calcula valores para tarefas semestrais
  const semestralPrevisto = contract.semestral_previsto || semestralTotal || 0;
  const semestralRealizado = contract.semestral_realizado || Math.round(contract.completed * 0.2) || 0;
  const semestralConcluido = contract.semestral_pct || contract.pct || 0;
  const semestralFaltam = Math.max(0, semestralPrevisto - semestralRealizado);
  const semestralDias = Math.ceil(semestralFaltam / 10) || 1; // Estimativa de 10 tarefas por dia
  
  // Valores para corretivas
  const corretivasRealizadas = contract.corretivas || Math.round(totalEquipments * 0.05) || 0;
  
  return {
    id: contract.id,
    name: contract.name,
    totalEquipments: totalEquipments,
    completedTasks: contract.completed || 0,
    percentCompleted: contract.pct || 0,
    // Dados estruturados por categoria
    taskCounts: {
      mensal: {
        previsto: mensalPrevisto,
        realizado: mensalRealizado,
        concluido: mensalConcluido,
        faltam: mensalFaltam,
        dias: mensalDias,
        total: mensalPrevisto
      },
      semestral: {
        previsto: semestralPrevisto,
        realizado: semestralRealizado,
        concluido: semestralConcluido,
        faltam: semestralFaltam,
        dias: semestralDias,
        total: semestralPrevisto
      },
      corretiva: {
        previsto: 0, // Corretivas não têm valor previsto
        realizado: corretivasRealizadas,
        concluido: 0,
        faltam: Math.round(corretivasRealizadas * 0.5) || 0,
        dias: 2,
        total: corretivasRealizadas
      }
    }
  };
};

const EquipmentTable = ({ contractsData, loading }) => {
  if (loading) {
    return <LinearProgress />;
  }
  
  console.log('Contratos recebidos em EquipmentTable:', contractsData);
  
  // Usa os dados reais de contratos em vez de dados estáticos
  // Cria setores dinâmicos a partir dos dados recebidos
  const sectors = contractsData && contractsData.length > 0 ? contractsData.map(contract => {
    // Processa os dados de cada contrato
    const processedData = getContractRealData(contract.id, contractsData);
    return processedData || {
      id: contract.id,
      name: contract.name || contract.description,
      totalEquipments: contract.total || 0,
      taskCounts: {
        mensal: { previsto: 0, realizado: 0, concluido: 0, faltam: 0, dias: 0, total: 0 },
        semestral: { previsto: 0, realizado: 0, concluido: 0, faltam: 0, dias: 0, total: 0 },
        corretiva: { previsto: 0, realizado: 0, concluido: 0, faltam: 0, dias: 0, total: 0 }
      }
    };
  }) : [];

  // Se não tiver nenhum dado, exibe mensagem
  if (sectors.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography variant="h6">Nenhum dado de contrato disponível.</Typography>
      </Box>
    );
  }
  
  return (
    <Box>
      <Typography variant="h6" align="center" gutterBottom sx={{ mt: 3, mb: 1, fontWeight: 'bold' }}>
        TOTAL DE EQUIPAMENTOS ATIVOS
      </Typography>
      
      {sectors.map((sector, index) => (
        <Box key={index} sx={{ mb: 4 }}>
          <Typography variant="h6" gutterBottom sx={{ mt: 2, color: '#1976d2', fontWeight: 'bold', textAlign: 'center' }}>
            SETOR: {sector.name}
          </Typography>
          
          <TableContainer component={Paper}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 'bold', backgroundColor: '#f5f5f5' }}>DESCRIÇÃO</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 'bold', backgroundColor: '#f5f5f5' }}>QTDE. PREV./MÊS</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 'bold', backgroundColor: '#f5f5f5' }}>QTDE. REALIZ./MÊS</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 'bold', backgroundColor: '#f5f5f5' }}>% CONCLUÍDAS</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 'bold', backgroundColor: '#f5f5f5' }}>QTDE PREV./DIA</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 'bold', backgroundColor: '#f5f5f5' }}>FALTAM FINALIZAR</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 'bold', backgroundColor: '#f5f5f5' }}>QTDE. DIAS TRAB.</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 'bold', backgroundColor: '#f5f5f5' }}>TOTAL</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {/* Row for Total */}
                <TableRow>
                  <TableCell colSpan="8" align="right" sx={{ fontWeight: 'bold' }}>{sector.totalEquipments}</TableCell>
                </TableRow>
                {/* Row for Preventiva Mensal */}
                <TableRow sx={{ backgroundColor: '#e8f5e9' }}>
                  <TableCell sx={{ fontWeight: 'bold' }}>PREVENTIVA MENSAL - {sector.name}</TableCell>
                  <TableCell align="center">{sector.taskCounts.mensal.previsto}</TableCell>
                  <TableCell align="center" sx={{ backgroundColor: '#ffccbc' }}>{sector.taskCounts.mensal.realizado}</TableCell>
                  <TableCell align="center" sx={{ backgroundColor: '#ffccbc' }}>{sector.taskCounts.mensal.concluido}%</TableCell>
                  <TableCell align="center">{sector.taskCounts.mensal.dias}</TableCell>
                  <TableCell align="center">{sector.taskCounts.mensal.faltam}</TableCell>
                  <TableCell align="center">{4}</TableCell>
                  <TableCell align="center">{sector.taskCounts.mensal.total}</TableCell>
                </TableRow>
                {/* Row for Preventiva Semestral */}
                <TableRow sx={{ backgroundColor: '#fff8e1' }}>
                  <TableCell sx={{ fontWeight: 'bold' }}>PREVENTIVA SEMESTRAL - {sector.name}</TableCell>
                  <TableCell align="center">{sector.taskCounts.semestral.previsto}</TableCell>
                  <TableCell align="center" sx={{ backgroundColor: '#ffccbc' }}>{sector.taskCounts.semestral.realizado}</TableCell>
                  <TableCell align="center" sx={{ backgroundColor: '#ffccbc' }}>{sector.taskCounts.semestral.concluido}%</TableCell>
                  <TableCell align="center">{sector.taskCounts.semestral.dias}</TableCell>
                  <TableCell align="center">{sector.taskCounts.semestral.faltam}</TableCell>
                  <TableCell align="center">{4}</TableCell>
                  <TableCell align="center">{sector.taskCounts.semestral.total}</TableCell>
                </TableRow>
                {/* Row for Corretivas */}
                <TableRow sx={{ backgroundColor: '#ffebee' }}>
                  <TableCell sx={{ fontWeight: 'bold' }}>CORRETIVAS - {sector.name}</TableCell>
                  <TableCell align="center">-</TableCell>
                  <TableCell align="center">{sector.taskCounts.corretiva.realizado || '-'}</TableCell>
                  <TableCell align="center">-</TableCell>
                  <TableCell align="center">{sector.taskCounts.corretiva.dias}</TableCell>
                  <TableCell align="center">{sector.taskCounts.corretiva.faltam}</TableCell>
                  <TableCell align="center">{4}</TableCell>
                  <TableCell align="center">{sector.taskCounts.corretiva.total}</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      ))}
    </Box>
  );
};

export default EquipmentTable;
