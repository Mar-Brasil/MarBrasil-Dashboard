import React from 'react';
import {
  Box, Grid, Paper, Typography, Card, CardContent,
  Divider, Chip, List, ListItem, ListItemText, ListItemIcon
} from '@mui/material';
import SchoolIcon from '@mui/icons-material/School';
import ComputerIcon from '@mui/icons-material/Computer';
import PersonIcon from '@mui/icons-material/Person';
import DescriptionIcon from '@mui/icons-material/Description';

// --- DADOS MOCKADOS PARA DEMONSTRAÇÃO DO FLUXO REAL ---
// Substitua futuramente por fetch em backend/API
const contracts = [
  {
    contractId: 1,
    contractName: 'STS36693/22 SETOR 01', // customer_groups.description
    schools: [
      {
        schoolId: 11827707,
        schoolName: 'EMEF JARDIM PAULISTANO', // customers.description
        managers: ['João Silva', 'Maria Oliveira'], // users.name
        equipments: ['Computador Dell i5', 'Projetor Epson X41', 'Impressora HP M428'], // equipments.name
      },
      {
        schoolId: 11827708,
        schoolName: 'EMEF VILA MEDEIROS', 
        managers: ['Carlos Santos'],
        equipments: ['Notebook Lenovo', 'Smart TV Samsung', 'Scanner Brother'],
      },
    ],
  },
  {
    contractId: 2,
    contractName: 'STS36694/22 SETOR 02',
    schools: [
      {
        schoolId: 11827709,
        schoolName: 'EMEF JARDIM BRASIL',
        managers: ['Ana Ferreira'],
        equipments: ['Computador HP', 'Projetor BenQ', 'Impressora Epson'],
      },
    ],
  },
];

export default function Dashboard() {
  return (
    <Box sx={{ p: 3, background: '#f5f5f5', minHeight: '100vh' }}>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 'bold', color: '#1976d2' }}>
        Dashboard de Contratos e Equipamentos
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          {/* Área principal - Contratos e Escolas */}
          {contracts.map(contract => (
            <Card key={contract.contractId} sx={{ mb: 3, borderRadius: 2, boxShadow: 3 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <DescriptionIcon sx={{ mr: 1, color: '#1976d2' }} />
                  <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
                    {contract.contractName}
                  </Typography>
                </Box>
                
                <Divider sx={{ mb: 2 }} />
                
                {contract.schools.map(school => (
                  <Paper key={school.schoolId} sx={{ mb: 2, p: 2, borderRadius: 2, bgcolor: '#f9f9f9' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <SchoolIcon sx={{ mr: 1, color: '#2e7d32' }} />
                      <Typography variant="h6">{school.schoolName}</Typography>
                    </Box>
                    
                    <Box sx={{ display: 'flex', flexDirection: 'column', ml: 4, mt: 1 }}>
                      {/* Responsáveis */}
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <PersonIcon sx={{ mr: 1, fontSize: 'small', color: '#5c6bc0' }} />
                        <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                          Responsáveis:
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, ml: 1 }}>
                          {school.managers.map((manager, idx) => (
                            <Chip 
                              key={idx} 
                              label={manager} 
                              size="small" 
                              sx={{ bgcolor: '#e3f2fd', fontSize: '0.75rem' }} 
                            />
                          ))}
                        </Box>
                      </Box>
                      
                      {/* Equipamentos */}
                      <Box sx={{ mt: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                          <ComputerIcon sx={{ mr: 1, fontSize: 'small', color: '#f57c00' }} />
                          <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                            Equipamentos:
                          </Typography>
                        </Box>
                        <List dense disablePadding sx={{ ml: 4 }}>
                          {school.equipments.map((equipment, idx) => (
                            <ListItem key={idx} disableGutters sx={{ py: 0.25 }}>
                              <ListItemIcon sx={{ minWidth: 24 }}>
                                <Box sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: '#f57c00' }} />
                              </ListItemIcon>
                              <ListItemText 
                                primary={equipment} 
                                primaryTypographyProps={{ variant: 'body2' }} 
                              />
                            </ListItem>
                          ))}
                        </List>
                      </Box>
                    </Box>
                  </Paper>
                ))}
              </CardContent>
            </Card>
          ))}
        </Grid>
        
        <Grid item xs={12} md={4}>
          {/* Área lateral - Estatísticas */}
          <Card sx={{ borderRadius: 2, boxShadow: 3, height: '100%' }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>
                Resumo
              </Typography>
              
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" color="text.secondary">Total de Contratos</Typography>
                <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#1976d2' }}>{contracts.length}</Typography>
              </Box>
              
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" color="text.secondary">Total de Escolas</Typography>
                <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#2e7d32' }}>
                  {contracts.reduce((total, contract) => total + contract.schools.length, 0)}
                </Typography>
              </Box>
              
              <Box>
                <Typography variant="subtitle2" color="text.secondary">Total de Equipamentos</Typography>
                <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#f57c00' }}>
                  {contracts.reduce((total, contract) => {
                    return total + contract.schools.reduce((schoolTotal, school) => {
                      return schoolTotal + school.equipments.length;
                    }, 0);
                  }, 0)}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
