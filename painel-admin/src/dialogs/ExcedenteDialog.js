import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  List,
  ListItem,
  ListItemText,
  Typography,
} from '@mui/material';

/**
 * Diálogo genérico para listar itens excedentes.
 * Props:
 *  - open: boolean
 *  - title: string
 *  - items: array of strings
 *  - onClose: function
 */
const ExcedenteDialog = ({ open, title, items = [], onClose }) => (
  <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
    <DialogTitle>{title}</DialogTitle>
    <DialogContent dividers>
      {items && items.length > 0 ? (
        <List>
          {items.map((item, idx) => (
            <ListItem divider key={idx}>
              <ListItemText primary={item} />
            </ListItem>
          ))}
        </List>
      ) : (
        <Typography>Detalhes do excedente não disponíveis.</Typography>
      )}
    </DialogContent>
  </Dialog>
);

export default ExcedenteDialog;
