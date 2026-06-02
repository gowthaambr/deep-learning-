import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';

// Fix for default marker icons in React Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface MapWidgetProps {
  center: { lat: number, lng: number };
  markers: { lat: number, lng: number, popup: string }[];
}

const MapWidget: React.FC<MapWidgetProps> = ({ center, markers }) => {
  return (
    <MapContainer center={[center.lat, center.lng]} zoom={12} style={{ height: '300px', width: '100%', borderRadius: '12px' }}>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {markers.map((m, idx) => (
        <Marker key={idx} position={[m.lat, m.lng]}>
          <Popup>{m.popup}</Popup>
        </Marker>
      ))}
    </MapContainer>
  );
};

export default MapWidget;
