import json
import re

html_file = r'c:\Users\DELL\RAG-GROWW\stitch_navi_mf_faq_assistant\navi_mf_assistant_chat_with_history_sidebar\code.html'
with open(html_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Extract the JSON config
match = re.search(r'tailwind\.config\s*=\s*(\{.*?\})\s*</script>', content, re.DOTALL)
if match:
    config_str = match.group(1)
    # Fix trailing commas to parse as json (very hacky, let's just do it cleanly)
    # Wait, the config in HTML is valid JS object but might not be valid JSON (has trailing commas, no quotes on keys)
    # Let's just use regex to extract colors.
    colors = re.findall(r'"([^"]+)"\s*:\s*"([^"]+)"', config_str)
    
    theme_css = "@import 'tailwindcss';\n\n"
    theme_css += "@theme {\n"
    for key, value in colors:
        if key in ["class", "DEFAULT", "lg", "xl", "full", "xs", "sm", "md", "unit", "gutter", "container-max", "headline-md", "body-md", "code-sm", "display-lg-mobile", "label-md", "body-lg", "display-lg"]:
            continue
        if value.startswith("#"):
            theme_css += f"  --color-{key}: {value};\n"
    theme_css += "}\n\n"

    # Also extract styles
    style_match = re.search(r'<style>(.*?)</style>', content, re.DOTALL)
    if style_match:
        theme_css += style_match.group(1)
        
    # Write to globals.css
    with open(r'c:\Users\DELL\RAG-GROWW\frontend\src\app\globals.css', 'w', encoding='utf-8') as out:
        out.write(theme_css)
    print("Successfully generated globals.css")
else:
    print("Could not find tailwind config")
