import React from 'react';
import { 
  Dialog, DialogTitle, DialogContent, DialogActions, Button, 
  Box, CircularProgress, List, ListItem, ListItemText, 
  Stepper, Step, StepLabel, StepConnector,
  Typography 
} from '@mui/material';
import { styled } from '@mui/material/styles';

const stepConnectorClasses = {
  alternativeLabel: 'MuiStepConnector-alternativeLabel',
  active: 'MuiStepConnector-active',
  completed: 'MuiStepConnector-completed',
  line: 'MuiStepConnector-line'
};

const ContractConnector = styled(StepConnector)(({ theme }) => ({
  [`&.${stepConnectorClasses.alternativeLabel}`]: {
    top: 10,
    left: 'calc(-50% + 16px)',
    right: 'calc(50% + 16px)',
  },
  [`& .${stepConnectorClasses.line}`]: {
    borderColor: theme.palette.mode === 'dark' ? theme.palette.grey[800] : '#eaeaf0',
    borderTopWidth: 3,
    borderRadius: 1,
  },
  [`&.${stepConnectorClasses.active}, &.${stepConnectorClasses.completed}`]: {
    [`& .${stepConnectorClasses.line}`]: {
      borderColor: theme.palette.primary.main,
    },
  },
}));

const ContractsProgressDialog = ({ open, onClose, data, loading }) => (
  <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
    <DialogTitle>Progresso de Contratos</DialogTitle>
    <DialogContent dividers>
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
          <CircularProgress />
        </Box>
      ) : (
        <List>
          {data.map(item => (
            <ListItem divider key={item.id} sx={{ flexDirection: 'column', alignItems: 'flex-start', py: 2 }}>
              <ListItemText
                primary={item.name}
                secondary={`${item.completed}/${item.total} (${item.pct}%)`}
              />
              <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                <Stepper 
                  alternativeLabel 
                  connector={<ContractConnector />} 
                  activeStep={(() => {
                    if (!item.total) return 0;
                    const ratio = item.completed / item.total;
                    if (ratio >= 0.75) return 3;
                    if (ratio >= 0.5) return 2;
                    if (ratio >= 0.25) return 1;
                    return 0;
                  })()} 
                  sx={{ flexGrow: 1, '.MuiStepConnector-line': { borderTopWidth: 3 }, mb: 1 }}
                >
                  {['1', '10', '20', '30/31'].map(label => (
                    <Step key={label}>
                      <StepLabel>{label}</StepLabel>
                    </Step>
                  ))}
                </Stepper>
              </Box>
            </ListItem>
          ))}
          {data.length === 0 && (
            <Typography>Nenhum dado disponível.</Typography>
          )}
        </List>
      )}
    </DialogContent>
    <DialogActions>
      <Button onClick={onClose}>Fechar</Button>
    </DialogActions>
  </Dialog>
);

export default ContractsProgressDialog;
