import React, { useEffect, useState } from "react";
import axios from "axios";
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Typography } from "@mui/material";

function extractFields(data) {
  const allFields = new Set();
  data.forEach(item => {
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

const Customers = () => {
  const [customers, setCustomers] = useState([]);
  const [columns, setColumns] = useState([]);

  useEffect(() => {
    let all = [];
    let page = 1;
    const fetchAll = () => {
      axios.get(`http://localhost:8000/api/customers?page=${page}&pageSize=100`)
        .then(res => {
          if (res.data.length > 0) {
            all = all.concat(res.data);
            page += 1;
            fetchAll();
          } else {
            setCustomers(all);
            setColumns(extractFields(all));
          }
        })
        .catch(() => {
          setCustomers([]);
          setColumns([]);
        });
    };
    fetchAll();
  }, []);

  return (
    <div>
      <Typography variant="h4" gutterBottom>Clientes</Typography>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              {columns.map(col => (
                <TableCell key={col}>{col}</TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {customers.map((customer, idx) => {
              let jsonObj = {};
              if (customer.json) {
                try {
                  jsonObj = typeof customer.json === "string" ? JSON.parse(customer.json) : customer.json;
                } catch {}
              }
              return (
                <TableRow key={customer.id || idx}>
                  {columns.map(col => (
                    <TableCell key={col}>
                      {customer[col] !== undefined
                        ? String(customer[col])
                        : jsonObj[col] !== undefined
                          ? (typeof jsonObj[col] === "object" ? JSON.stringify(jsonObj[col]) : String(jsonObj[col]))
                          : ""
                      }
                    </TableCell>
                  ))}
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  );
};

export default Customers;
