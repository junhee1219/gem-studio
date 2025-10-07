from fastapi.responses import FileResponse
from settings import PAGES_DIR

def html_page(file_name):
    return FileResponse(PAGES_DIR / file_name)