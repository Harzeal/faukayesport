"use client";
import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    const res = await fetch('/api/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });

    const data = await res.json();

    if (res.ok) {
      // Cek peran dari database (Admin atau Karyawan)
      if (data.user.peran === 'admin') {
        router.push('/dashboard-admin');
      } else {
        router.push('/dashboard-karyawan');
      }
    } else {
      alert("Login Gagal: " + data.message);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <form onSubmit={handleLogin} className="bg-white p-8 rounded-xl shadow-md border w-96">
        <h2 className="text-2xl font-bold mb-6 text-gray-800">Login Faukay Esport</h2>
        <input 
          type="text" placeholder="Username" 
          className="w-full p-2 mb-4 border rounded text-black"
          onChange={(e) => setUsername(e.target.value)}
        />
        <input 
          type="password" placeholder="Password" 
          className="w-full p-2 mb-6 border rounded text-black"
          onChange={(e) => setPassword(e.target.value)}
        />
        <button 
          disabled={loading}
          className="w-full bg-blue-600 text-white py-2 rounded-lg font-semibold hover:bg-blue-700"
        >
          {loading ? 'Memproses...' : 'Masuk Sekarang'}
        </button>
      </form>
    </div>
  );
}
