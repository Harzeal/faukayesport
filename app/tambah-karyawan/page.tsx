"use client";

import { useState } from "react";

export default function TambahKaryawanPage() {
  // Anggap saja kita mengambil data user dari session nanti
  const [role, setRole] = useState("admin"); 

  if (role !== "admin") {
    return <p className="p-10 text-red-500">Akses Ditolak! Hanya Admin yang boleh menambah karyawan.</p>;
  }

  return (
    <div className="p-10">
      <h1 className="text-2xl font-bold mb-4">Tambah Karyawan Baru</h1>
      <form className="flex flex-col gap-4 max-w-sm">
        <input className="border p-2 text-black" type="text" placeholder="Username Karyawan" />
        <input className="border p-2 text-black" type="password" placeholder="Password Karyawan" />
        <button className="bg-blue-500 text-white p-2 rounded">Simpan Akun</button>
      </form>
    </div>
  );
}
