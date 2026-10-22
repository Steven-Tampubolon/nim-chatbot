# nim-chatbot

## Deskripsi
nim-chatbot adalah antarmuka terminal (REPL) untuk mengobrol dengan model
NVIDIA NIM. Riwayat percakapan dikirim ke API NVIDIA melalui `NimClient`
dan jawaban ditampilkan secara bertahap (streaming). Percakapan dapat
disimpan dan dimuat kembali lewat perintah `/save` dan `/load`.

## Instalasi
Butuh Python 3.12. Pasang dependensi runtime dengan:

```
pip install -r requirements.txt
```

## Konfigurasi
Chatbot dikonfigurasi lewat lima variabel lingkungan berikut.

| Variabel | Wajib | Nilai bawaan |
| --- | --- | --- |
| `NVIDIA_API_KEY` | Wajib | (tidak ada) |
| `NVIDIA_MODEL` | Tidak | `z-ai/glm-5.3` |
| `NVIDIA_BASE_URL` | Tidak | `https://integrate.api.nvidia.com/v1` |
| `CHATBOT_SYSTEM_PROMPT` | Tidak | Kamu adalah asisten yang ramah dan ringkas. Jawab dalam bahasa yang dipakai pengguna. |
| `CHATBOT_MAX_HISTORY_CHARS` | Tidak | `12000` |

`NVIDIA_API_KEY` wajib diatur sebelum menjalankan chatbot. Salin
`.env.example` sebagai titik awal, lalu isi kunci Anda di variabel tersebut.
Jangan menulis kunci API di berkas yang di-commit; simpan hanya sebagai
variabel lingkungan.

## Menjalankan
Jalankan chatbot dari akar repo dengan:

```
python -m nim_chatbot
```

Opsi `--model` dapat dipakai untuk mengganti model hanya pada sesi itu:

```
python -m nim_chatbot --model <nama-model>
```

## Perintah di dalam chatbot
| Perintah | Fungsi |
| --- | --- |
| `/help` | Menampilkan daftar perintah |
| `/reset` | Mengosongkan riwayat percakapan |
| `/save <berkas>` | Menyimpan percakapan ke berkas |
| `/load <berkas>` | Memuat percakapan dari berkas |
| `/exit` | Keluar dari chatbot |

## Menjalankan tes
Jalankan seluruh tes tanpa jaringan dengan:

```
python -m pytest -q
```
