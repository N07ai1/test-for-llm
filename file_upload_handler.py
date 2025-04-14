from fastapi import UploadFile, HTTPException
from fastapi.responses import JSONResponse

class FileUploadHandler:
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
    
    @staticmethod
    def allowed_file(filename: str) -> bool:
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in FileUploadHandler.ALLOWED_EXTENSIONS
    
    @staticmethod
    async def handle_upload(file: UploadFile):
        if not FileUploadHandler.allowed_file(file.filename):
            raise HTTPException(status_code=400, detail="文件类型不支持，仅支持PDF、DOCX和TXT文件")
        
        try:
            contents = await file.read()
            # 在实际应用中，这里应该将文件保存到指定目录
            # 例如：with open(f"uploads/{file.filename}", "wb") as f:
            #         f.write(contents)
            return JSONResponse(
                status_code=200,
                content={"message": "文件上传成功", "filename": file.filename}
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")