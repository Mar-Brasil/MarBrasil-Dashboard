import React, { useEffect, useState } from "react";
import axios from "axios";
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Typography, Button, Dialog, DialogTitle, DialogContent, DialogActions, TextField, MenuItem, Select, InputLabel, FormControl, Checkbox, ListItemText, OutlinedInput, IconButton } from "@mui/material";
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';

// Função utilitária para "achatar" o JSON em colunas simples (apenas 1º nível)
function extractFields(data) {
  const allFields = new Set();
  data.forEach(item => {
    // Pega campos do registro e do JSON bruto
    Object.keys(item).forEach(k => {
      if (k !== "json") allFields.add(k);
    });
    if (item.json) {
      try {
        const jsonObj = typeof item.json === "string" ? JSON.parse(item.json) : item.json;
        Object.keys(jsonObj).forEach(k => allFields.add(k));
      } catch {}
    }
  });
  return Array.from(allFields);
}


const PERMISSOES_OPCOES = [
  'Dashboard',
  'Baixar Tarefas',
  'Tempo Real',
  'Equipamentos',
  'Faturamento',
  'Admin Faturamento',
  'Semestral',
];

const Users = () => {
  const [users, setUsers] = useState([]);
  const [contracts, setContracts] = useState([]);
  const [open, setOpen] = useState(false);
  const [editUser, setEditUser] = useState(null);
  const [form, setForm] = useState({
    nome_completo: '',
    cpf: '',
    data_nascimento: '',
    foto: '',
    username: '',
    senha: '',
    permissoes: [],
    contratos: [],
  });

  const fetchUsers = () => {
    axios.get("http://localhost:8000/usuarios")
      .then(res => setUsers(res.data))
      .catch(() => setUsers([]));
  };

  const fetchContracts = () => {
    axios.get("http://localhost:8000/api/contracts")
      .then(res => setContracts(res.data || [])) // API retorna um array diretamente
      .catch(() => setContracts([]));
  };

  useEffect(() => { 
    fetchUsers(); 
    fetchContracts(); 
  }, []);

  const handleOpen = (user = null) => {
    setEditUser(user);
    // Garante que o campo 'contratos' exista no formulário, mesmo que o usuário não tenha nenhum.
    const formInitialState = user 
      ? { ...user, senha: '', contratos: user.contratos || [] } 
      : { nome_completo: '', cpf: '', data_nascimento: '', foto: '', username: '', senha: '', permissoes: [], contratos: [] };
    setForm(formInitialState);
    setOpen(true);
  };
  const handleClose = () => { setOpen(false); setEditUser(null); };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm({ ...form, [name]: value });
  };
  const handlePermissoesChange = (e) => {
    setForm({ ...form, permissoes: e.target.value });
  };

  const handleContratosChange = (e) => {
    setForm({ ...form, contratos: e.target.value });
  };
  const handleFotoChange = (e) => {
    setForm({ ...form, foto: e.target.value }); // Simples: salva o caminho/nome
  };

  const handleSubmit = () => {
    const payload = { ...form };
    if (!payload.nome_completo || !payload.cpf || !payload.username || !payload.senha) return;
    if (editUser) {
      axios.put(`http://localhost:8000/usuarios/${editUser.id}`, payload).then(() => { fetchUsers(); handleClose(); });
    } else {
      axios.post("http://localhost:8000/usuarios", payload).then(() => { fetchUsers(); handleClose(); });
    }
  };
  const handleDelete = (id) => {
    if (window.confirm("Tem certeza que deseja deletar este usuário?")) {
      axios.delete(`http://localhost:8000/usuarios/${id}`).then(fetchUsers);
    }
  };

  return (
    <div>
      <Typography variant="h4" gutterBottom>Usuários</Typography>
      <Button variant="contained" color="primary" onClick={() => handleOpen()}>Novo Usuário</Button>
      <TableContainer component={Paper} sx={{ mt: 2 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Nome Completo</TableCell>
              <TableCell>CPF</TableCell>
              <TableCell>Data Nasc.</TableCell>
              <TableCell>Foto</TableCell>
              <TableCell>Usuário</TableCell>
              <TableCell>Permissões</TableCell>
              <TableCell>Ações</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {users.map((user) => (
              <TableRow key={user.id}>
                <TableCell>{user.nome_completo}</TableCell>
                <TableCell>{user.cpf}</TableCell>
                <TableCell>{user.data_nascimento}</TableCell>
                <TableCell>{user.foto ? <img src={user.foto} alt="foto" style={{ width: 32, height: 32, borderRadius: '50%' }} /> : '-'}</TableCell>
                <TableCell>{user.username}</TableCell>
                <TableCell>{user.permissoes.join(', ')}</TableCell>
                <TableCell>
                  <IconButton onClick={() => handleOpen(user)}><EditIcon /></IconButton>
                  <IconButton onClick={() => handleDelete(user.id)}><DeleteIcon /></IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>{editUser ? 'Editar Usuário' : 'Novo Usuário'}</DialogTitle>
        <DialogContent>
          <TextField label="Nome Completo" name="nome_completo" value={form.nome_completo} onChange={handleChange} fullWidth margin="dense" required />
          <TextField label="CPF" name="cpf" value={form.cpf} onChange={handleChange} fullWidth margin="dense" required />
          <TextField label="Data de Nascimento" name="data_nascimento" type="date" value={form.data_nascimento || ''} onChange={handleChange} fullWidth margin="dense" InputLabelProps={{ shrink: true }} />
          <TextField label="Caminho da Foto" name="foto" value={form.foto} onChange={handleFotoChange} fullWidth margin="dense" />
          <TextField label="Nome de Usuário" name="username" value={form.username} onChange={handleChange} fullWidth margin="dense" required />
          <TextField label="Senha" name="senha" type="password" value={form.senha} onChange={handleChange} fullWidth margin="dense" required />
          <FormControl fullWidth margin="dense">
            <InputLabel>Permissões</InputLabel>
            <Select
              multiple
              value={form.permissoes}
              onChange={handlePermissoesChange}
              input={<OutlinedInput label="Permissões" />}
              renderValue={(selected) => selected.join(', ')}
            >
              {PERMISSOES_OPCOES.map((name) => (
                <MenuItem key={name} value={name}>
                  <Checkbox checked={form.permissoes.indexOf(name) > -1} />
                  <ListItemText primary={name} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl fullWidth margin="dense">
            <InputLabel>Contratos</InputLabel>
            <Select
              multiple
              value={form.contratos}
              onChange={handleContratosChange}
              input={<OutlinedInput label="Contratos" />}
              renderValue={(selected) => selected.map(id => contracts.find(c => c.id === id)?.name).filter(Boolean).join(', ')}
            >
              {contracts.map((contract) => (
                <MenuItem key={contract.id} value={contract.id}>
                  <Checkbox checked={form.contratos.indexOf(contract.id) > -1} />
                  <ListItemText primary={contract.name} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancelar</Button>
          <Button onClick={handleSubmit} variant="contained" color="primary">Salvar</Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};

export default Users;
