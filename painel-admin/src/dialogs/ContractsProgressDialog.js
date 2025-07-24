import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  Box,
  CircularProgress,
  Typography,
  Button,
  Stepper,
  Step,
  StepLabel,
  StepConnector,
} from '@mui/material';
import { styled } from '@mui/material/styles';

// Conector customizado (mantém a mesma aparência da versão inline)
const ContractConnector = styled(StepConnector)(({ theme }) => ({
  [`.${StepConnector.line}`]: {
    borderTopWidth: 3,
    borderColor: theme.palette.grey[400],
  },
  [`&.active .${StepConnector.line}`]: {
    borderColor: theme.palette.primary.main,
  },
  [`&.completed .${StepConnector.line}`]: {
    borderColor: theme.palette.primary.main,
  },
}));

/**
 * Dialog que exibe progresso por contrato.
 * Props:
 *  - open: boolean
 *  - loading: boolean
 *  - data: [{ id, name, completed, total, pct }]
 *  - onClose: func
 */
const ContractsProgressDialog = ({ open, loading, data = [], onClose }) => (
  <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
    <DialogTitle>Progresso de Contratos</DialogTitle>
    <DialogContent dividers>
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
          <CircularProgress />
        </Box>
      ) : (
        <List>
          {data.map((item) => (
            <ListItem key={item.id} divider>
              <ListItemText
                primary={item.name}
                secondary={`${item.completed}/${item.total} (${item.pct}%)`}
              />
              <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1, ml: 2 }}>
                <Stepper
                  alternativeLabel
                  activeStep={Math.min(3, Math.floor((item.pct / 100) * 4))}
                  connector={<ContractConnector />}
                  sx={{ width: '100%' }}
                >
                  {['1', '10', '20', '30/31'].map((label) => (
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
