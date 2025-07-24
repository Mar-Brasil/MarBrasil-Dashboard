import React from 'react';
import { Grid } from '@mui/material';
import KpiCard from './KpiCard';
import SchoolIcon from '@mui/icons-material/School';
import PeopleIcon from '@mui/icons-material/People';
import BuildIcon from '@mui/icons-material/Build';
import AssignmentIcon from '@mui/icons-material/Assignment';

// Espera props: indicadores = { tarefas, colaboradores, equipamentos, escolas }
const Indicadores = ({ indicadores }) => (
  <Grid container spacing={2} sx={{ mb: 2 }}>
    <Grid item xs={12} sm={6} md={3}>
      <KpiCard
        title="Tarefas"
        value={indicadores.tarefas}
        icon={<AssignmentIcon color="primary" sx={{ fontSize: 32 }} />}
      />
    </Grid>
    <Grid item xs={12} sm={6} md={3}>
      <KpiCard
        title="Colaboradores"
        value={indicadores.colaboradores}
        icon={<PeopleIcon color="secondary" sx={{ fontSize: 32 }} />}
      />
    </Grid>
    <Grid item xs={12} sm={6} md={3}>
      <KpiCard
        title="Equipamentos"
        value={indicadores.equipamentos}
        icon={<BuildIcon color="action" sx={{ fontSize: 32 }} />}
      />
    </Grid>
    <Grid item xs={12} sm={6} md={3}>
      <KpiCard
        title="Escolas"
        value={indicadores.escolas}
        icon={<SchoolIcon color="success" sx={{ fontSize: 32 }} />}
      />
    </Grid>
  </Grid>
);

export default Indicadores;