import React, { useEffect, useState, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup, CircleMarker } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import io from 'socket.io-client';

const SOCKET_URL = 'http://localhost:4000'; // backend local
const MAP_CENTER = [-23.9608, -46.3336]; // Centro inicial: Santos/SP (empresa)
const MAP_ZOOM = 12;

export default function TempoReal() {
  const [markers, setMarkers] = useState([]);

  useEffect(() => {
    const socket = io(SOCKET_URL);
    socket.on('auvo-task-event', (payload) => {
      if (
        payload?.result?.Entities &&
        Array.isArray(payload.result.Entities)
      ) {
        const novasTarefas = payload.result.Entities.map((task) => ({
          id: task.taskID,
          lat: task.latitude,
          lng: task.longitude,
          orientation: task.orientation,
          checkIn: task.checkIn,
          checkInDate: task.checkInDate,
        }));
        setMarkers((prev) => [
          ...prev.filter(
            (m) => !novasTarefas.some((t) => t.id === m.id)
          ),
          ...novasTarefas,
        ]);
      }
    });
    return () => socket.disconnect();
  }, []);

  const renderMarkers = useCallback(() =>
    markers.map((marker) =>
      marker.lat && marker.lng ? (
        <CircleMarker
          key={marker.id}
          center={[marker.lat, marker.lng]}
          radius={12}
          color="#1fa31f"
          fillColor="#2ecc40"
          fillOpacity={0.9}
          stroke={true}
        >
          <Popup>
            <b>Tarefa:</b> {marker.orientation}<br />
            <b>Responsável:</b> {marker.nomeUsuario || marker.idUserFrom}<br />
            {marker.checkIn && marker.checkInDate && (
              <span><b>Check-in:</b> {new Date(marker.checkInDate).toLocaleString()}<br /></span>
            )}
            {marker.checkOut && marker.checkOutDate && (
              <span><b>Check-out:</b> {new Date(marker.checkOutDate).toLocaleString()}<br /></span>
            )}
            {marker.tempoExecucao !== undefined && marker.tempoExecucao !== null && (
              <span><b>Tempo de execução:</b> {marker.tempoExecucao} min<br /></span>
            )}
            <b>Status:</b> {marker.finished ? 'Finalizada' : 'Em andamento'}<br />
            <b>Endereço:</b> {marker.address || '-'}
          </Popup>
        </CircleMarker>
      ) : null
    ),
    [markers]
  );

  return (
    <div style={{ padding: 20 }}>
      <h2>Tempo Real - Tarefas no Mapa (OpenStreetMap)</h2>
      <MapContainer center={MAP_CENTER} zoom={MAP_ZOOM} style={{ width: '100%', height: '80vh' }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {renderMarkers()}
      </MapContainer>
    </div>
  );
}
