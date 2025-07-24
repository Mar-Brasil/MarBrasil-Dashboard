// Este arquivo contém apenas o trecho modificado da tabela de valores
// Você precisará substituir este trecho no arquivo FaturamentoReport.js

                    <TableBody>
                      <TableRow>
                        <TableCell>PREV MENSAL</TableCell>
                        <TableCell align="right">{processedData.indicators.active_equipment || 0}</TableCell>
                        <TableCell align="right">R$ 8,50</TableCell>
                        <TableCell align="right">R$ 3,50</TableCell>
                        <TableCell align="right">{`R$ ${((processedData.indicators.active_equipment || 0) * 8.5 + (processedData.indicators.active_equipment || 0) * 3.5).toFixed(2).replace('.', ',')}`}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>EXCEDENTE</TableCell>
                        <TableCell align="right">{processedData.indicators.open_tasks || 0}</TableCell>
                        <TableCell align="right">R$ 10,75</TableCell>
                        <TableCell align="right">R$ -</TableCell>
                        <TableCell align="right">{`R$ ${((processedData.indicators.open_tasks || 0) * 10.75).toFixed(2).replace('.', ',')}`}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>PREV SEMESTRAL</TableCell>
                        <TableCell align="right">{processedData.indicators.completed_tasks || 0}</TableCell>
                        <TableCell align="right">R$ 8,50</TableCell>
                        <TableCell align="right">R$ 3,50</TableCell>
                        <TableCell align="right">{`R$ ${((processedData.indicators.completed_tasks || 0) * 8.5 + (processedData.indicators.completed_tasks || 0) * 3.5).toFixed(2).replace('.', ',')}`}</TableCell>
                      </TableRow>
