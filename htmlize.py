import html

def generate_html():
    # Read the response from response.txt
    try:
        with open('response.txt', 'r') as file:
            content = file.read()
    except FileNotFoundError:
        print("Error: response.txt file not found.")
        return
    except IOError:
        print("Error: Unable to read response.txt file.")
        return

    # Split the content into response and summary
    parts = content.split("SUMMARY OF PROCESS")
    response = parts[0].strip()
    summary = parts[1].strip() if len(parts) > 1 else ""

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>COT Python Script Response</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; }}
            h1, h2 {{ color: #333; }}
            .section {{ background-color: #f0f0f0; padding: 15px; margin-bottom: 20px; }}
            .section p {{ font-size: 0.9em; }}
            .metadata {{ font-weight: bold; margin-left: 20px; }}
        </style>
    </head>
    <body>
        <h1>COT Python Script Response</h1>
        <div class="section">
            <h2>Response</h2>
            <p>{html.escape(response).replace('**', '<strong>').replace('</strong>**', '</strong>').replace('\n\n', '</p><p>').replace('\n', '<br>')}</p>
        </div>
        <div class="section">
            <h2>Summary of Process</h2>
            <p>{html.escape(summary).replace('**', '<strong>').replace('</strong>**', '</strong>').replace('\n\n', '</p><p>').replace('\n', '<br>')}</p>
        </div>
        <div class="metadata">
            <p><strong>Model:</strong> meta.llama3-70b-instruct-v1:0</p>
            <p><strong>Input tokens:</strong> 698</p>
            <p><strong>Output tokens:</strong> 478</p>
            <p><strong>Total tokens:</strong> 1176</p>
            <p><strong>Stop reason:</strong> end_turn</p>
        </div>
    </body>
    </html>
    """
    
    # Write the HTML content to response.html
    try:
        with open('response.html', 'w') as f:
            f.write(html_content)
        print("HTML file 'response.html' has been generated successfully.")
    except IOError:
        print("Error: Unable to write to response.html file.")

# Run the function to generate the HTML file
generate_html()