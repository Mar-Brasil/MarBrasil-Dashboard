import React from 'react';
import { Drawer, List, ListItem, ListItemIcon, ListItemText, Toolbar } from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import PeopleIcon from '@mui/icons-material/People';
import CloudDownloadIcon from '@mui/icons-material/CloudDownload';
import AssessmentIcon from '@mui/icons-material/Assessment';
import DevicesOtherIcon from '@mui/icons-material/DevicesOther';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import BusinessIcon from '@mui/icons-material/Business';
import CalendarViewWeekIcon from '@mui/icons-material/CalendarViewWeek';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import GroupIcon from '@mui/icons-material/Group';
import SettingsIcon from '@mui/icons-material/Settings';
import DescriptionIcon from '@mui/icons-material/Description';
import { Link, useLocation } from 'react-router-dom';

const menu = [
  { text: 'Dashboard', icon: DashboardIcon, path: '/' },
  { text: 'Usuários', icon: PeopleIcon, path: '/users' },
  { text: 'Baixar Tarefas', icon: CloudDownloadIcon, path: '/download-tasks' },
  { text: 'Tempo Real', icon: AssessmentIcon, path: '/tempo-real' },
  // { text: 'Clientes', icon: BusinessIcon, path: '/customers' },
  // { text: 'Equipes', icon: GroupIcon, path: '/teams' },
  { text: 'Equipamentos', icon: DevicesOtherIcon, path: '/faturamento' },
  { text: 'Faturamento', icon: AttachMoneyIcon, path: '/faturamento-report' },

  { text: 'Admin Faturamento', icon: SettingsIcon, path: '/admin-faturamento' },
  { text: 'Semestral', icon: CalendarViewWeekIcon, path: '/semestral' },
  { text: 'Semestral Geral', icon: CalendarTodayIcon, path: '/semestral-geral' },
  { text: 'Mensal Geral', icon: CalendarTodayIcon, path: '/mensal-geral' },
  // { text: 'Configurações', icon: SettingsIcon, path: '/settings' }
];

export default function Sidebar() {
  const location = useLocation();
  return (
    <Drawer variant="permanent" sx={{ width: 240, [`& .MuiDrawer-paper`]: { width: 240, boxSizing: 'border-box' } }}>
      <Toolbar />
      <List>
        {menu.map(item => {
          const IconComponent = item.icon;
          const selected = location.pathname === item.path;
          return (
            <ListItem button key={item.text} component={Link} to={item.path} selected={selected}>
              <ListItemIcon>
                <IconComponent color={selected ? 'primary' : 'inherit'} />
              </ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItem>
          );
        })}
      </List>
    </Drawer>
  );
}
