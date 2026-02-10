"use client";
import { useState } from 'react';

export default function AdminDashboard() {
  const [items, setItems] = useState([
    { id: 1, nama: "Mouse Gaming Pro", stok: 10, ket: "Kondisi Baru" },
  ]);

  const tambahBarang = () => {
    const nama = prompt("Nama Barang:");
    if (nama) {
      setItems([...items, { id: Date.now(), nama, stok: 0, ket: "Barang Baru" }]);
    }
  };

  const hapusBarang = (id: number) => {
    if(confirm("Hapus barang ini?")) {
      setItems(items.filter(item => item.id !== id));
    }
  };

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-blue-700">Dashboard Admin (Full Access)</h1>
        <button onClick={tambahBarang} className="bg-blue-600 text-white px-4 py-2 rounded-lg">+ Tambah Barang</button>
      </div>

      <table className="w-full bg-white shadow rounded-lg overflow-hidden">
        <thead className="bg-blue-100">
          <tr>
            <th className="p-3 text-left">Nama Barang</th>
            <th className="p-3 text-left">Keterangan</th>
            <th className="p-3 text-center">Stok</th>
            <th className="p-3 text-center">Aksi</th>
          </tr>
        </thead>
        <tbody>
          {items.map(item => (
            <tr key={item.id} className="border-b">
              <td className="p-3 font-semibold">{item.nama}</td>
              <td className="p-3 text-gray-600">{item.ket}</td>
              <td className="p-3 text-center font-mono">{item.stok}</td>
              <td className="p-3 text-center space-x-2">
                <button className="text-blue-500 hover:underline">Edit Ket</button>
                <button onClick={() => hapusBarang(item.id)} className="text-red-500 hover:underline">Hapus</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
