import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Typography, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from '@mui/material';

export default function Teams() {
  const [teams, setTeams] = useState([]);
  useEffect(() => {
    axios.get('http://localhost:8000/api/teams').then(res => setTeams(res.data));
  }, []);
  return (
    <div>
      <Typography variant="h5" gutterBottom>Equipes</Typography>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Nome</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {teams.map(team => (
              <TableRow key={team.id}>
                <TableCell>{team.id}</TableCell>
                <TableCell>{team.description}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  );
}
