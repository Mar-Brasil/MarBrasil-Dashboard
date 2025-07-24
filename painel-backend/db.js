import sqlite3 from 'sqlite3';
import { open } from 'sqlite';

// Função para abrir conexão com o banco
export async function openDb() {
  return open({
    filename: '../auvo.db',
    driver: sqlite3.Database
  });
}

// Função para buscar nome do usuário pelo ID
export async function getUserNameById(userId) {
  const db = await openDb();
  const user = await db.get('SELECT name FROM users WHERE userId = ?', userId);
  await db.close();
  return user ? user.name : null;
}
