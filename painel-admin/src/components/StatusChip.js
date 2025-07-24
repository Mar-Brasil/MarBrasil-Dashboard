import React from 'react';
import PropTypes from 'prop-types';
import Chip from '@mui/material/Chip';

/**
 * Displays a colored status indicator chip based on the task status ID.
 * Extracted from Dashboard.js for reuse and better modularity.
 */
const StatusChip = ({ status }) => {
  const statusMap = {
    1: { label: 'Aberta', color: 'default' },
    2: { label: 'Em Deslocamento', color: 'info' },
    3: { label: 'Check-in', color: 'info' },
    5: { label: 'Finalizada', color: 'success' },
    6: { label: 'Concluída', color: 'success' },
    7: { label: 'Cancelada', color: 'error' },
  };
  const { label = 'N/A', color = 'default' } = statusMap[status] || {};
  return <Chip label={label} color={color} size="small" />;
};

StatusChip.propTypes = {
  status: PropTypes.number.isRequired,
};

export default StatusChip;
