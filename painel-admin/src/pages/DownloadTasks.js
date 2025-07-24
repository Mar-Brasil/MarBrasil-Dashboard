import React, { useState, useEffect, useRef } from 'react';
import {
  Box, Paper, Typography, Button, LinearProgress, TextField, Alert, List, ListItem, ListItemText, Chip
} from '@mui/material';
import CloudDownloadIcon from '@mui/icons-material/CloudDownload';
import dayjs from 'dayjs';
import axios from 'axios';
import io from 'socket.io-client';

// Conecta ao servidor de Socket.IO
const socket = io('http://localhost:3001');

export default function DownloadTasks() {
  const today = dayjs();
  const [startDate, setStartDate] = useState(today.startOf('month').format('YYYY-MM-DD'));
  const [endDate, setEndDate] = useState(today.endOf('month').format('YYYY-MM-DD'));
  
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState([]);
  const [status, setStatus] = useState('idle'); // idle, loading, done, error
  const [error, setError] = useState(null);
  const logsEndRef = useRef(null);

  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [logs]);

  useEffect(() => {
    socket.on('progress', (data) => {
      if (data.message) {
        setLogs(prevLogs => [...prevLogs, data.message]);
      }
      if (data.percentage) {
        setProgress(data.percentage);
      }
      if (data.error) {
        setError(data.message);
        setStatus('error');
      }
      if (data.percentage === 100) {
        setStatus('done');
      }
    });

    return () => {
      socket.off('progress');
    };
  }, []);

  const handleDownload = async () => {
    setStatus('loading');
    setLogs([]);
    setProgress(0);
    setError(null);

    try {
      await axios.post('/api/download-tasks', {
        startDate,
        endDate,
      });
    } catch (err) {
      const errorMessage = err.response?.data?.message || 'Erro ao conectar com o servidor.';
      setStatus('error');
      setError(errorMessage);
      setLogs(prevLogs => [...prevLogs, errorMessage]);
    }
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', mt: 4 }}>
      <Paper sx={{ p: 3, mb: 2 }}>
        <Typography variant="h5" gutterBottom>
          Baixar Tarefas do Auvo
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Selecione um período e inicie o download para sincronizar as tarefas do Auvo com o banco de dados local.
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, mb: 3, alignItems: 'center' }}>
          <TextField
            label="Data Inicial"
            type="date"
            value={startDate}
            onChange={e => setStartDate(e.target.value)}
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            label="Data Final"
            type="date"
            value={endDate}
            onChange={e => setEndDate(e.target.value)}
            InputLabelProps={{ shrink: true }}
          />
          <Button
            variant="contained"
            color="primary"
            startIcon={<CloudDownloadIcon />}
            onClick={handleDownload}
            disabled={status === 'loading'}
            sx={{ height: '56px' }}
          >
            Baixar Tarefas
          </Button>
        </Box>

        {(status === 'loading' || status === 'done' || status === 'error') && (
          <Box sx={{ mt: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Box sx={{ width: '100%', mr: 1 }}>
                    <LinearProgress variant="determinate" value={progress} />
                </Box>
                <Box sx={{ minWidth: 35 }}>
                    <Typography variant="body2" color="text.secondary">{`${Math.round(progress)}%`}</Typography>
                </Box>
            </Box>

            {logs.length > 0 && (
              <Paper variant="outlined" sx={{ mt: 2, p: 2, maxHeight: 300, overflowY: 'auto', backgroundColor: 'grey.100' }}>
                <List dense>
                  {logs.map((log, index) => (
                    <ListItem key={index} sx={{ py: 0.5 }}>
                      <ListItemText primaryTypographyProps={{ fontSize: '0.875rem', fontFamily: 'monospace' }} primary={log} />
                    </ListItem>
                  ))}
                  <div ref={logsEndRef} />
                </List>
              </Paper>
            )}
          </Box>
        )}

        {status === 'done' && (
          <Alert severity="success" sx={{ mt: 2 }}>
            Sincronização concluída com sucesso!
          </Alert>
        )}
        {status === 'error' && error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
      </Paper>
    </Box>
  );
}
