from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import uopy
from ..database import get_database_connection
from ..auth.jwt import jwt_handler

router = APIRouter(
    prefix="/files",
    tags=["files"],
    responses={404: {"description": "Not found"}},
)

class FileContent(BaseModel):
    content: str
    version: str = "25.04.46.1"  # Following our versioning convention

class FileInfo(BaseModel):
    name: str
    type: str
    size: int
    last_modified: str
    version: str
    attributes: Dict[str, Any]

@router.get("/", response_model=List[FileInfo])
async def list_files(
    path: str = "",
    current_user: Dict[str, Any] = Depends(jwt_handler.get_current_user)
):
    """List files in a directory."""
    try:
        with get_database_connection() as conn:
            # Use LIST to get file information
            cmd = uopy.Command(f"LIST {path}")
            cmd.run()
            
            # Parse the LIST output and return structured data
            files = []
            for line in cmd.response.split("\n"):
                if not line.strip():
                    continue
                    
                # Parse file information from LIST output
                # Format: filename^type^size^date^time^attributes
                parts = line.split("^")
                if len(parts) >= 5:
                    files.append({
                        "name": parts[0],
                        "type": parts[1],
                        "size": int(parts[2]),
                        "last_modified": f"{parts[3]} {parts[4]}",
                        "version": "25.04.46.1",  # This should be read from the file
                        "attributes": {}  # Additional attributes can be parsed here
                    })
            
            return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{file_id}", response_model=FileContent)
async def get_file(
    file_id: str,
    current_user: Dict[str, Any] = Depends(jwt_handler.get_current_user)
):
    """Get file content."""
    try:
        with get_database_connection() as conn:
            # Read the file content
            cmd = uopy.Command(f"READ {file_id}")
            cmd.run()
            
            if not cmd.response:
                raise HTTPException(status_code=404, detail="File not found")
            
            # Get file version from VOC
            version_cmd = uopy.Command(f"READ VOC {file_id}")
            version_cmd.run()
            version = "25.04.46.1"  # Default version
            if version_cmd.response:
                # Parse version from VOC record
                # Format: program^version^attributes
                parts = version_cmd.response.split("^")
                if len(parts) > 1:
                    version = parts[1]
            
            return {
                "content": cmd.response,
                "version": version
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{file_id}", response_model=FileContent)
async def create_file(
    file_id: str,
    content: FileContent,
    current_user: Dict[str, Any] = Depends(jwt_handler.get_current_user)
):
    """Create a new file."""
    try:
        with get_database_connection() as conn:
            # Write the file content
            cmd = uopy.Command(f"WRITE {content.content} TO {file_id}")
            cmd.run()
            
            # Update VOC record with version
            voc_cmd = uopy.Command(f"WRITE {file_id}^{content.version}^CREATED TO VOC {file_id}")
            voc_cmd.run()
            
            return {
                "content": content.content,
                "version": content.version
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{file_id}", response_model=FileContent)
async def update_file(
    file_id: str,
    content: FileContent,
    current_user: Dict[str, Any] = Depends(jwt_handler.get_current_user)
):
    """Update file content."""
    try:
        with get_database_connection() as conn:
            # Check if file exists
            check_cmd = uopy.Command(f"READ {file_id}")
            check_cmd.run()
            if not check_cmd.response:
                raise HTTPException(status_code=404, detail="File not found")
            
            # Write the updated content
            cmd = uopy.Command(f"WRITE {content.content} TO {file_id}")
            cmd.run()
            
            # Update VOC record with new version
            voc_cmd = uopy.Command(f"WRITE {file_id}^{content.version}^UPDATED TO VOC {file_id}")
            voc_cmd.run()
            
            return {
                "content": content.content,
                "version": content.version
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    current_user: Dict[str, Any] = Depends(jwt_handler.get_current_user)
):
    """Delete a file."""
    try:
        with get_database_connection() as conn:
            # Delete the file
            cmd = uopy.Command(f"DELETE {file_id}")
            cmd.run()
            
            # Delete VOC record
            voc_cmd = uopy.Command(f"DELETE VOC {file_id}")
            voc_cmd.run()
            
            return {"message": "File deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{file_id}/history", response_model=List[Dict[str, Any]])
async def get_file_history(
    file_id: str,
    current_user: Dict[str, Any] = Depends(jwt_handler.get_current_user)
):
    """Get file version history."""
    try:
        with get_database_connection() as conn:
            # Read from MVEDITOR.HISTORY
            cmd = uopy.Command(f"SELECT MVEDITOR.HISTORY WITH @ID = '{file_id}'")
            cmd.run()
            
            history = []
            for record in cmd.response.split("\n"):
                if not record.strip():
                    continue
                    
                # Parse history record
                # Format: file_id^version^timestamp^user^action^changes
                parts = record.split("^")
                if len(parts) >= 6:
                    history.append({
                        "version": parts[1],
                        "timestamp": parts[2],
                        "user": parts[3],
                        "action": parts[4],
                        "changes": parts[5]
                    })
            
            return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 