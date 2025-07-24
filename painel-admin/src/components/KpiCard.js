import React from 'react';
import { Card, Box } from '@mui/material';

const KpiCard = ({ title, value, icon, extra = null }) => (
  <Card variant="outlined" sx={{ p: { xs: 1, sm: 2 }, height: '100%' }}>
    <Box sx={{
      display: 'flex',
      flexDirection: { xs: 'column', sm: 'row' },
      alignItems: { xs: 'center', sm: 'center' },
      justifyContent: { xs: 'center', sm: 'space-between' },
      textAlign: { xs: 'center', sm: 'left' },
      gap: 1,
    }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        {icon}
        <Box>
          <Box sx={{ fontSize: 12, color: 'text.secondary' }}>{title}</Box>
          <Box sx={{ fontWeight: 'bold' }}>{value}</Box>
        </Box>
      </Box>
      {extra}
    </Box>
  </Card>
);

export default KpiCard;
