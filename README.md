uvicorn main:app --host 127.0.0.1 --port 8000 --reload

nohup uvicorn main:app \
  --host 127.0.0.1 \
  --port 8000 \
  > uvicorn.log 2>&1 &

ps aux | grep uvicorn

sudo vim /etc/nginx/sites-enabled/fastapi
UPLOAD_DIR = "/mnt/disk-rendi/uploads"