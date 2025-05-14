from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import uopy
from ..database import get_database_connection
from ..auth.jwt import jwt_handler

router = APIRouter(
    prefix="/editor",
    tags=["editor"],
    responses={404: {"description": "Not found"}},
)

class CompletionRequest(BaseModel):
    file_id: str
    line: int
    column: int
    prefix: str

class CompletionItem(BaseModel):
    label: str
    kind: str
    detail: str
    documentation: Optional[str] = None
    insertText: str
    sortText: str

class SyntaxToken(BaseModel):
    line: int
    startColumn: int
    endColumn: int
    scopes: List[str]

@router.post("/completion", response_model=List[CompletionItem])
async def get_completions(
    request: CompletionRequest,
    current_user: Dict[str, Any] = Depends(jwt_handler.get_current_user)
):
    """Get code completions for the current cursor position."""
    try:
        with get_database_connection() as conn:
            # Get the current file content
            cmd = uopy.Command(f"READ {request.file_id}")
            cmd.run()
            
            if not cmd.response:
                raise HTTPException(status_code=404, detail="File not found")
            
            # Get completions based on context
            completions = []
            
            # 1. Built-in MVBasic functions and statements
            builtins = [
                {"label": "OPEN", "kind": "keyword", "detail": "OPEN statement", 
                 "documentation": "Opens a file for reading or writing", "insertText": "OPEN"},
                {"label": "READ", "kind": "keyword", "detail": "READ statement",
                 "documentation": "Reads data from a file", "insertText": "READ"},
                {"label": "WRITE", "kind": "keyword", "detail": "WRITE statement",
                 "documentation": "Writes data to a file", "insertText": "WRITE"},
                # Add more built-ins here
            ]
            
            # 2. User-defined subroutines and functions
            # Read VOC to get available programs
            voc_cmd = uopy.Command("LIST VOC")
            voc_cmd.run()
            user_defs = []
            for line in voc_cmd.response.split("\n"):
                if not line.strip():
                    continue
                parts = line.split("^")
                if len(parts) > 0:
                    user_defs.append({
                        "label": parts[0],
                        "kind": "function",
                        "detail": f"User-defined {parts[0]}",
                        "documentation": f"Defined in {parts[0]}",
                        "insertText": parts[0]
                    })
            
            # 3. Variables in current scope
            # This would require parsing the current file to find variables
            # For now, we'll return a placeholder
            variables = [
                {"label": "VERSION", "kind": "variable", "detail": "Program version",
                 "documentation": "Current program version", "insertText": "VERSION"}
            ]
            
            # Combine all completions
            all_completions = builtins + user_defs + variables
            
            # Filter based on prefix
            filtered_completions = [
                CompletionItem(
                    label=item["label"],
                    kind=item["kind"],
                    detail=item["detail"],
                    documentation=item.get("documentation"),
                    insertText=item["insertText"],
                    sortText=item["label"].lower()
                )
                for item in all_completions
                if item["label"].lower().startswith(request.prefix.lower())
            ]
            
            return filtered_completions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/syntax", response_model=List[SyntaxToken])
async def get_syntax_tokens(
    file_id: str,
    current_user: Dict[str, Any] = Depends(jwt_handler.get_current_user)
):
    """Get syntax highlighting tokens for the file."""
    try:
        with get_database_connection() as conn:
            # Get the file content
            cmd = uopy.Command(f"READ {file_id}")
            cmd.run()
            
            if not cmd.response:
                raise HTTPException(status_code=404, detail="File not found")
            
            # Parse the content and generate syntax tokens
            tokens = []
            lines = cmd.response.split("\n")
            
            # MVBasic syntax highlighting rules
            keywords = {
                "OPEN", "READ", "WRITE", "CLOSE", "CLEAR", "STOP", "END",
                "IF", "THEN", "ELSE", "END", "FOR", "NEXT", "LOOP", "WHILE",
                "REPEAT", "UNTIL", "GOTO", "GOSUB", "RETURN", "CALL", "SUBROUTINE",
                "FUNCTION", "PROGRAM", "EQUATE", "COMMON", "DIMENSION", "MAT"
            }
            
            operators = {"=", "+", "-", "*", "/", "<", ">", "<=", ">=", "<>", "EQ", "NE", "GT", "GE", "LT", "LE"}
            
            for line_num, line in enumerate(lines, 1):
                # Tokenize the line
                current_pos = 0
                while current_pos < len(line):
                    # Skip whitespace
                    while current_pos < len(line) and line[current_pos].isspace():
                        current_pos += 1
                    
                    if current_pos >= len(line):
                        break
                    
                    # Check for keywords
                    for keyword in keywords:
                        if line[current_pos:].upper().startswith(keyword):
                            tokens.append(SyntaxToken(
                                line=line_num,
                                startColumn=current_pos,
                                endColumn=current_pos + len(keyword),
                                scopes=["keyword.mvbasic"]
                            ))
                            current_pos += len(keyword)
                            break
                    
                    # Check for operators
                    for operator in operators:
                        if line[current_pos:].startswith(operator):
                            tokens.append(SyntaxToken(
                                line=line_num,
                                startColumn=current_pos,
                                endColumn=current_pos + len(operator),
                                scopes=["operator.mvbasic"]
                            ))
                            current_pos += len(operator)
                            break
                    
                    # Check for strings
                    if line[current_pos] == '"':
                        end_pos = line.find('"', current_pos + 1)
                        if end_pos == -1:
                            end_pos = len(line)
                        tokens.append(SyntaxToken(
                            line=line_num,
                            startColumn=current_pos,
                            endColumn=end_pos + 1,
                            scopes=["string.mvbasic"]
                        ))
                        current_pos = end_pos + 1
                        continue
                    
                    # Check for numbers
                    if line[current_pos].isdigit():
                        end_pos = current_pos
                        while end_pos < len(line) and (line[end_pos].isdigit() or line[end_pos] == '.'):
                            end_pos += 1
                        tokens.append(SyntaxToken(
                            line=line_num,
                            startColumn=current_pos,
                            endColumn=end_pos,
                            scopes=["number.mvbasic"]
                        ))
                        current_pos = end_pos
                        continue
                    
                    # Default to identifier
                    end_pos = current_pos
                    while end_pos < len(line) and (line[end_pos].isalnum() or line[end_pos] == '_'):
                        end_pos += 1
                    if end_pos > current_pos:
                        tokens.append(SyntaxToken(
                            line=line_num,
                            startColumn=current_pos,
                            endColumn=end_pos,
                            scopes=["identifier.mvbasic"]
                        ))
                        current_pos = end_pos
                    else:
                        current_pos += 1
            
            return tokens
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate")
async def validate_code(
    file_id: str,
    current_user: Dict[str, Any] = Depends(jwt_handler.get_current_user)
):
    """Validate MVBasic code for syntax errors."""
    try:
        with get_database_connection() as conn:
            # Get the file content
            cmd = uopy.Command(f"READ {file_id}")
            cmd.run()
            
            if not cmd.response:
                raise HTTPException(status_code=404, detail="File not found")
            
            # Use Universe's BASIC compiler to validate
            validate_cmd = uopy.Command(f"BASIC {file_id} VALIDATE")
            validate_cmd.run()
            
            # Parse validation results
            errors = []
            if validate_cmd.response:
                for line in validate_cmd.response.split("\n"):
                    if "ERROR" in line.upper():
                        # Parse error line
                        # Format: Line X: Error message
                        parts = line.split(":", 1)
                        if len(parts) == 2:
                            line_num = int(parts[0].split()[1])
                            message = parts[1].strip()
                            errors.append({
                                "line": line_num,
                                "message": message,
                                "severity": "error"
                            })
            
            return {
                "valid": len(errors) == 0,
                "errors": errors
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 