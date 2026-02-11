import { supabase } from '@/lib/supabase';

export async function POST(request: Request) {
  const { username, password, role } = await request.json();

  // Memasukkan data karyawan baru ke tabel 'pengguna'
  const { data, error } = await supabase
    .from('pengguna')
    .insert([{ 
        "Nama belakang": username, 
        "Kata sandi": password, 
        "peran": 'karyawan' 
    }]);

  if (error) return Response.json({ error: error.message }, { status: 400 });
  return Response.json({ message: "Akun Karyawan Berhasil Dibuat!" });
}