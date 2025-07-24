import React, { useState } from 'react';
import { 
  Box, Typography, Chip, Tooltip, IconButton, Accordion, AccordionSummary, AccordionDetails, 
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Link, 
  LinearProgress, Badge
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import BuildIcon from '@mui/icons-material/Build';
import ArticleIcon from '@mui/icons-material/Article';
import EventRepeatIcon from '@mui/icons-material/EventRepeat';
import CalendarViewWeekIcon from '@mui/icons-material/CalendarViewWeek';
import { specialTaskIconsConfig, getPercentageColor, cleanSchoolName, getEquipmentCount } from '../utils/dashboardUtils';
import StatusChip from './StatusChip';
import { formatDate } from '../utils/dashboardUtils';

const SchoolRow = ({ school, taskTypeMap, selectedContractInfo, dateRange }) => {
  const [expanded, setExpanded] = useState(false);
  
  // Função utilitária para identificar equipamentos ativos (aceita vários formatos)
  const isAtivo = (equip) => {
    if (!equip) return false;
    if (typeof equip === 'string') {
      return equip.toLowerCase().includes('ativo');
    }
    if (equip.status) {
      return equip.status.toLowerCase().includes('ativo');
    }
    return false;
  };

  // Ordenar tarefas por data (mais recente primeiro)
  const sortedTasks = [...(school.tasks || [])].sort((a, b) => {
    const dateA = new Date(a.checkInDate || a.lastUpdate);
    const dateB = new Date(b.checkInDate || b.lastUpdate);
    return dateB - dateA;
  });

  // Obter ícones de tarefas especiais para a escola
  const getSchoolIcons = () => {
    const icons = [];
    Object.entries(specialTaskIconsConfig).forEach(([key, config]) => {
      const hasTask = (school.tasks || []).some(task => 
        task.orientation && task.orientation.toUpperCase().includes(key)
      );
      if (hasTask) {
        icons.push(
          <Tooltip key={key} title={config.tooltip}>
            <config.Icon sx={{ color: config.color }} />
          </Tooltip>
        );
      }
    });
    return icons;
  };

  return (
    <Accordion expanded={expanded} onChange={() => setExpanded(!expanded)}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="subtitle1">
            {cleanSchoolName(school.school_info.description)}
          </Typography>
          <Box sx={{ display: 'flex', gap: 0.5 }}>
            {getSchoolIcons()}
          </Box>
        </Box>
      </AccordionSummary>
      <AccordionDetails>
        <TableContainer component={Paper} variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Tarefa</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Data</TableCell>
                <TableCell>Equipamentos</TableCell>
                <TableCell>Ações</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {sortedTasks.map((task, idx) => (
                <TableRow key={`${task.id}-${idx}`}>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Typography variant="body2">
                        {task.orientation || 'Tarefa sem descrição'}
                      </Typography>
                      {task.taskType && (
                        <Tooltip title={taskTypeMap[task.taskType]?.name || 'Tipo desconhecido'}>
                          <Chip 
                            label={taskTypeMap[task.taskType]?.abbreviation || '?'} 
                            size="small" 
                            sx={{ ml: 1 }} 
                          />
                        </Tooltip>
                      )}
                    </Box>
                  </TableCell>
                  <TableCell>
                    <StatusChip status={task.taskStatus} />
                  </TableCell>
                  <TableCell sx={{ whiteSpace: 'nowrap' }}>
                    {formatDate(task.checkInDate || task.lastUpdate)}
                  </TableCell>
                  <TableCell>
                    {getEquipmentCount(task)}
                  </TableCell>
                  <TableCell>
                    <Tooltip title="Ver detalhes da tarefa">
                      <IconButton size="small" onClick={() => window.open(task.taskUrl, '_blank')}>
                        <InfoOutlinedIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </AccordionDetails>
    </Accordion>
  );
};

export default SchoolRow;
