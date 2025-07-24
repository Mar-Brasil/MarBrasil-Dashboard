import React from 'react';
import { Grid } from '@mui/material';
import KpiCard from './KpiCard';
import ArticleIcon from '@mui/icons-material/Article'; // PMOC
import EventRepeatIcon from '@mui/icons-material/EventRepeat'; // Mensal
import CalendarViewWeekIcon from '@mui/icons-material/CalendarViewWeek'; // Semestral
import BuildIcon from '@mui/icons-material/Build'; // Corretiva

// Espera props: customKpis (objeto), openExDialog (função), mensalItems, semestralItems, pmocItems
const KpiCustomCards = ({
  customKpis,
  openExDialog,
  mensalItems = [],
  semestralItems = [],
  pmocItems = []
}) => (
  <Grid container spacing={2} sx={{ mb: 2 }}>
    <Grid item xs={12} sm={6} md={3}>
      <KpiCard
        title="Mensal"
        value={customKpis.mensal}
        icon={<EventRepeatIcon color="success" sx={{ fontSize: 32 }} />}
        extra={mensalItems.length > 0 ? (
          <span onClick={() => openExDialog('Excedentes Mensal', mensalItems)} style={{ cursor: 'pointer', color: '#1976d2', fontWeight: 600 }}>
            +{mensalItems.length}
          </span>
        ) : null}
      />
    </Grid>
    <Grid item xs={12} sm={6} md={3}>
      <KpiCard
        title="Semestral"
        value={customKpis.semestral}
        icon={<CalendarViewWeekIcon color="info" sx={{ fontSize: 32 }} />}
        extra={semestralItems.length > 0 ? (
          <span onClick={() => openExDialog('Excedentes Semestral', semestralItems)} style={{ cursor: 'pointer', color: '#1976d2', fontWeight: 600 }}>
            +{semestralItems.length}
          </span>
        ) : null}
      />
    </Grid>
    <Grid item xs={12} sm={6} md={3}>
      <KpiCard
        title="PMOC"
        value={customKpis.pmoc}
        icon={<ArticleIcon color="warning" sx={{ fontSize: 32 }} />}
        extra={pmocItems.length > 0 ? (
          <span onClick={() => openExDialog('Excedentes PMOC', pmocItems)} style={{ cursor: 'pointer', color: '#1976d2', fontWeight: 600 }}>
            +{pmocItems.length}
          </span>
        ) : null}
      />
    </Grid>
    <Grid item xs={12} sm={6} md={3}>
      <KpiCard
        title="Corretiva"
        value={customKpis.corretiva}
        icon={<BuildIcon color="error" sx={{ fontSize: 32 }} />}
      />
    </Grid>
  </Grid>
);

export default KpiCustomCards;