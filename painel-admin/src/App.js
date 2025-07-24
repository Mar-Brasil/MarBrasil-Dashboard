import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Users from './pages/Users';
import DownloadTasks from './pages/DownloadTasks';
import BillingReport from './pages/BillingReport';
import FaturamentoReport from './pages/FaturamentoReport';
import SemestralPlanner from './pages/SemestralPlanner';
import SemestralGeral from './pages/SemestralGeral';
import MensalGeral from './pages/MensalGeral';
import Customers from './pages/Customers';
import Teams from './pages/Teams';
import Settings from './pages/Settings';
import BillingAdmin from './pages/BillingAdmin';
import TempoReal from './pages/TempoReal';

import { Box } from '@mui/material';

function App() {
  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      <Sidebar />
      <Box component="main" sx={{ flexGrow: 1, bgcolor: '#f5f6fa', p: 3 }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/users" element={<Users />} />
          <Route path="/download-tasks" element={<DownloadTasks />} />
          <Route path="/tempo-real" element={<TempoReal />} />
          <Route path="/faturamento" element={<BillingReport />} />
          <Route path="/faturamento-report" element={<FaturamentoReport />} />

          <Route path="/admin-faturamento" element={<BillingAdmin />} />
          <Route path="/semestral" element={<SemestralPlanner />} />
          <Route path="/semestral-geral" element={<SemestralGeral />} />
          <Route path="/mensal-geral" element={<MensalGeral />} />
          <Route path="/customers" element={<Customers />} />
          <Route path="/teams" element={<Teams />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </Box>
    </Box>
  );
}

export default App;
