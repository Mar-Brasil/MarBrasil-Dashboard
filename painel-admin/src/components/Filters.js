import React from 'react';
import { Box, Chip, Typography } from '@mui/material';

// Espera props: colaboradores, colaboradoresSelecionados, onColaboradorToggle, tiposTarefa, tiposSelecionados, onTipoToggle
const Filters = ({
  colaboradores = [],
  colaboradoresSelecionados = [],
  onColaboradorToggle,
  tiposTarefa = [],
  tiposSelecionados = [],
  onTipoToggle
}) => (
  <Box sx={{ mb: 2 }}>
    <Typography variant="subtitle1" sx={{ mb: 1 }}>Colaboradores:</Typography>
    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
      {colaboradores.map(colab => (
        <Chip
          key={colab.id}
          label={colab.nome}
          color={colaboradoresSelecionados.includes(colab.id) ? 'primary' : 'default'}
          onClick={() => onColaboradorToggle(colab.id)}
          clickable
        />
      ))}
    </Box>
    <Typography variant="subtitle1" sx={{ mb: 1 }}>Tipos de Tarefa:</Typography>
    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
      {tiposTarefa.map(tipo => (
        <Chip
          key={tipo.id}
          label={tipo.nome}
          color={tiposSelecionados.includes(tipo.id) ? 'secondary' : 'default'}
          onClick={() => onTipoToggle(tipo.id)}
          clickable
        />
      ))}
    </Box>
  </Box>
);

export default Filters;