import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  List,
  ListItem,
  ListItemText,
  Typography
} from '@mui/material';

const ExcedenteDialog = ({ open, onClose, title, items }) => (
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
