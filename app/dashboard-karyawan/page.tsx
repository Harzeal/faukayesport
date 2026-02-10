"use client";
import { useState } from 'react';

export default function KaryawanDashboard() {
  const [items, setItems] = useState([
    { id: 1, nama: "Mouse Gaming Pro", stok: 10, ket: "Kondisi Baru" },
    { id: 2, nama: "Keyboard Mechanical", stok: 5, ket: "Switch Blue" },
  ]);

  const updateStok = (id: number, delta: number) => {
    setItems(items.map(item => 
      item.id === id ? { ...item, stok: Math.max(0, item.stok + delta) } : item
    ));
  };

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <h1 className="text-2xl font-bold mb-6 text-green-700">Dashboard Karyawan</h1>
      <div className="grid gap-4">
        {items.map(item => (
          <div key={item.id} className="bg-white p-4 shadow rounded-lg flex justify-between items-center">
            <div>
              <h3 className="font-bold">{item.nama}</h3>
              <p className="text-sm text-gray-500">{item.ket}</p>
            </div>
            <div className="flex items-center gap-4">
              <span className="font-mono text-xl">Stok: {item.stok}</span>
              <div className="flex gap-2">
                <button onClick={() => updateStok(item.id, -1)} className="bg-gray-200 px-3 py-1 rounded">-</button>
                <button onClick={() => updateStok(item.id, 1)} className="bg-green-500 text-white px-3 py-1 rounded">+</button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
