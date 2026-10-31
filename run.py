import os
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from app import tao_app

app = tao_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Hệ thống Quản lý Cơ sở Vật chất NEU đang chạy tại: http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
