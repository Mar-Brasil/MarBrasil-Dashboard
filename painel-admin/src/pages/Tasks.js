import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Typography, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from '@mui/material';

export default function Tasks() {
  const [tasks, setTasks] = useState([]);
  useEffect(() => {
    axios.get('http://localhost:8000/api/tasks').then(res => setTasks(res.data));
  }, []);
  return (
    <div>
      <Typography variant="h5" gutterBottom>Tarefas</Typography>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Usuário</TableCell>
              <TableCell>Descrição</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {tasks.map(task => (
              <TableRow key={task.id}>
                <TableCell>{task.id}</TableCell>
                <TableCell>{task.user_id}</TableCell>
                <TableCell>{task.description}</TableCell>
                <TableCell>{task.taskStatus}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  );
}
