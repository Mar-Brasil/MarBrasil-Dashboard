import React, { useState } from 'react';
import {
  Box, Grid, Paper, Typography, MenuItem, FormControl, Select, InputLabel, AppBar, Toolbar, Button,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, TablePagination
} from '@mui/material';
import { Bar, Pie, Doughnut, Line } from 'react-chartjs-2';
import 'chart.js/auto';

// --- DADOS MOCKADOS PARA DEMONSTRAÃ‡ÃƒO ---
const kpis = [
  { label: 'Escolas Atendidas', value: 4, color: '#1976d2', icon: 'ðŸ«' },
  { label: 'Total de Equipamentos Ativos', value: 0, color: '#d32f2f', icon: 'ðŸ–¥ï¸' },
  { label: 'TÃ©cnicos Ativos', value: 4, color: '#8e24aa', icon: 'ðŸ‘·' },
  { label: 'Taxa de ConclusÃ£o', value: '40%', color: '#388e3c', icon: 'âœ”ï¸' },
];
const setores = [
  { nome: 'Setor 1', qtd: 0 },
  { nome: 'Setor 2', qtd: 0 },
  { nome: 'Setor 3', qtd: 0 },
  { nome: 'Setor 4', qtd: 0 },
  { nome: 'Setor 5', qtd: 0 },
];
const estatisticas = [
  { label: 'Preventivas/MÃªs', value: 1200 },
  { label: 'Realizadas', value: 210 },
  { label: 'Pendentes', value: 35 },
];
const donutStatus = {
  labels: ['Finalizadas', 'Pendentes', 'Aguardando'],
  datasets: [{ data: [10, 5, 7], backgroundColor: ['#388e3c', '#fbc02d', '#757575'] }],
};
const topEscolas = {
  labels: ['Escola A', 'Escola B', 'Escola C', 'Escola D', 'Escola E'],
  datasets: [{ label: 'Volume de Tarefas', data: [30, 25, 20, 15, 10], backgroundColor: '#1976d2' }],
};
const tarefasTempo = {
  labels: ['01/05', '05/05', '10/05', '15/05', '20/05', '25/05', '30/05'],
  datasets: [{ label: 'Tarefas', data: [5, 8, 6, 10, 12, 9, 4], fill: true, borderColor: '#1976d2', backgroundColor: 'rgba(25, 118, 210, 0.1)' }],
};
const desempenhoSetor = {
  labels: ['Setor 1', 'Setor 2', 'Setor 3', 'Setor 4', 'Setor 5'],
  datasets: [{ label: 'Preventivas Mensais', data: [20, 15, 12, 8, 7], backgroundColor: '#43a047' }],
};
const tipoTarefa = {
  labels: ['ManutenÃ§Ã£o Preventiva', 'ManutenÃ§Ã£o Corretiva', 'InstalaÃ§Ã£o'],
  datasets: [{ data: [15, 10, 8], backgroundColor: ['#1976d2', '#8e24aa', '#d32f2f'] }],
};
const tarefasDetalhes = [
  { data: '01/06/2025', tecnico: 'TÃ©c. 1', escola: 'Escola Municipal Zona Norte 1', tipo: 'ManutenÃ§Ã£o Preventiva', obs: 'InspeÃ§Ã£o e verificaÃ§Ã£o.', status: 'Pendente', equipamentos: 'N/A', link: '#' },
  { data: '02/06/2025', tecnico: 'TÃ©c. 2', escola: 'Escola Municipal Zona Norte 2', tipo: 'ManutenÃ§Ã£o Corretiva', obs: 'Troca de equipamento.', status: 'Finalizada', equipamentos: 'N/A', link: '#' },
  { data: '03/06/2025', tecnico: 'TÃ©c. 3', escola: 'Escola Municipal Zona Norte 3', tipo: 'InstalaÃ§Ã£o', obs: 'Novo equipamento instalado.', status: 'Finalizada', equipamentos: 'N/A', link: '#' },
  { data: '04/06/2025', tecnico: 'TÃ©c. 1', escola: 'Escola Municipal Zona Norte 1', tipo: 'ManutenÃ§Ã£o Corretiva', obs: 'Ajuste de software.', status: 'Pendente', equipamentos: 'N/A', link: '#' },
];

function Dashboard() {
  const [unidade, setUnidade] = useState('Todos');
  const [setor, setSetor] = useState('Todos');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(5);

  return (
    <Box sx={{ background: '#f5f6fa', minHeight: '100vh' }}>
      {/* Header Azul */}
      <AppBar position="static" color="primary" sx={{ mb: 3 }}>
        <Toolbar sx={{ justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>Dashboard de ManutenÃ§Ã£o</Typography>
            <Typography variant="caption">Monitoramento de CondiÃ§Ãµes em Escolas PÃºblicas</Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <FormControl size="small" sx={{ minWidth: 120, bgcolor: 'white', borderRadius: 1 }}>
              <InputLabel>Unidade</InputLabel>
              <Select value={unidade} label="Unidade" onChange={e => setUnidade(e.target.value)}>
                <MenuItem value="Todos">Todos</MenuItem>
                <MenuItem value="Unidade 1">Unidade 1</MenuItem>
                <MenuItem value="Unidade 2">Unidade 2</MenuItem>
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 120, bgcolor: 'white', borderRadius: 1 }}>
              <InputLabel>Setor</InputLabel>
              <Select value={setor} label="Setor" onChange={e => setSetor(e.target.value)}>
                <MenuItem value="Todos">Todos</MenuItem>
                {setores.map(s => <MenuItem key={s.nome} value={s.nome}>{s.nome}</MenuItem>)}
              </Select>
            </FormControl>
          </Box>
        </Toolbar>
      </AppBar>

      {/* KPIs */}
      <Grid container spacing={2} sx={{ mb: 1 }}>
        {kpis.map((k, i) => (
          <Grid item xs={12} sm={6} md={3} key={i}>
            <Paper sx={{ p: 2, borderTop: `4px solid ${k.color}`, minHeight: 80, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">{k.label}</Typography>
                <Typography variant="h4" sx={{ fontWeight: 700 }}>{k.value}</Typography>
              </Box>
              <Box sx={{ fontSize: 32 }}>{k.icon}</Box>
            </Paper>
          </Grid>
        ))}
      </Grid>

      {/* Cards de Setor */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 600 }}>Equipamentos por Setor</Typography>
        <Grid container spacing={2}>
          {setores.map((s, i) => (
            <Grid item xs={12} sm={6} md={2.4} key={i}>
              <Paper sx={{ p: 2, textAlign: 'center', bgcolor: '#e3eafc' }}>
                <Typography variant="body1" fontWeight={600}>{s.nome}</Typography>
                <Typography variant="h5">{s.qtd}</Typography>
                <Typography variant="caption">Equipamentos</Typography>
              </Paper>
            </Grid>
          ))}
        </Grid>
      </Paper>

      {/* EstatÃ­sticas Preventivas */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2}>
          {estatisticas.map((e, i) => (
            <Grid item xs={12} md={4} key={i}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="subtitle2" color="text.secondary">{e.label} - Todos/2025</Typography>
                <Typography variant="h3" sx={{ color: '#1976d2', fontWeight: 700 }}>{e.value}</Typography>
              </Box>
            </Grid>
          ))}
        </Grid>
      </Paper>

      {/* GrÃ¡ficos principais */}
      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2">DistribuiÃ§Ã£o por Status</Typography>
            <Doughnut data={donutStatus} />
          </Paper>
        </Grid>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2">Top 10 Escolas por Volume de Tarefas</Typography>
            <Bar data={topEscolas} options={{ responsive: true, plugins: { legend: { display: false } } }} />
          </Paper>
        </Grid>
      </Grid>

      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2">Volume de Tarefas ao Longo do Tempo</Typography>
            <Line data={tarefasTempo} options={{ responsive: true, plugins: { legend: { display: false } } }} />
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2">DistribuiÃ§Ã£o por Tipo de Tarefa</Typography>
            <Pie data={tipoTarefa} />
          </Paper>
        </Grid>
      </Grid>

      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2">Desempenho por Setor - Preventivas Mensais (Junho/2025)</Typography>
            <Bar data={desempenhoSetor} options={{ responsive: true, plugins: { legend: { display: false } } }} />
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2">DistribuiÃ§Ã£o por Tipo de Tarefa</Typography>
            <Pie data={tipoTarefa} />
          </Paper>
        </Grid>
      </Grid>

      {/* Tabela detalhada */}
      <Paper sx={{ p: 2, mb: 4 }}>
        <Typography variant="subtitle2" sx={{ mb: 1 }}>Detalhes das Tarefas</Typography>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Data</TableCell>
                <TableCell>TÃ©cnico</TableCell>
                <TableCell>Escola</TableCell>
                <TableCell>Tipo de Tarefa</TableCell>
                <TableCell>ObservaÃ§Ã£o</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Equipamentos</TableCell>
                <TableCell>Link</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {tarefasDetalhes.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage).map((row, idx) => (
                <TableRow key={idx}>
                  <TableCell>{row.data}</TableCell>
                  <TableCell>{row.tecnico}</TableCell>
                  <TableCell>{row.escola}</TableCell>
                  <TableCell>{row.tipo}</TableCell>
                  <TableCell>{row.obs}</TableCell>
                  <TableCell>{row.status}</TableCell>
                  <TableCell>{row.equipamentos}</TableCell>
                  <TableCell><Button size="small" href={row.link} target="_blank">GO</Button></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          component="div"
          count={tarefasDetalhes.length}
          page={page}
          onPageChange={(e, newPage) => setPage(newPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={e => { setRowsPerPage(parseInt(e.target.value, 10)); setPage(0); }}
          rowsPerPageOptions={[5, 10, 25]}
        />
      </Paper>
    </Box>
  );
}

export default Dashboard;
