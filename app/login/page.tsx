"use client";
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-xl shadow-md text-center border border-gray-200">
        <h2 className="text-2xl font-bold mb-6 text-gray-800">Pilih Akses Masuk</h2>
        <div className="flex flex-col gap-4">
          <button 
            onClick={() => router.push('/dashboard-admin')}
            className="bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 transition"
          >
            Masuk sebagai Admin
          </button>
          <button 
            onClick={() => router.push('/dashboard-karyawan')}
            className="bg-green-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-green-700 transition"
          >
            Masuk sebagai Karyawan
          </button>
        </div>
      </div>
    </div>
  );
}
