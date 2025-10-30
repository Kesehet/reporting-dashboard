UPLOAD_FORM_HTML = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Upload File</title>
</head>
<body>
    <h1>Upload a File</h1>
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="file" required>
        <input type="submit" value="Upload">
    </form>
</body>
</html>
"""

def beautify_response(resp):
    """
    Beautify the response for better readability.
    """
    return f"<div style='color:green;background-color:black; padding:16px; font-family:monospace;'>{resp}</div>"