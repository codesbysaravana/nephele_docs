To process the resume located at C:/your_location, make sure your Nephele backend server is running (usually via uvicorn app.main:app --reload or by running main.py).

Once the server is running (assuming it's on the default port 8000), you can upload the resume using either PowerShell or Command Prompt (curl).

Option 1: Using PowerShell (Recommended on Windows) Open PowerShell and run the following command:

powershell


Invoke-RestMethod -Uri "http://localhost:8000/resume/upload" `
  -Method Post `
  -Form @{
      file = Get-Item -Path "C:\your_path"
  }
Option 2: Using standard curl If you prefer curl or are using an environment that supports it:

bash


curl -X 'POST' \
  'http://localhost:8000/resume/upload' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@C:/your_path'
