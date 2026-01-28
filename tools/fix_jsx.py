
path = r"c:\AI Fusion Labs\X AGENTS\X Agent Factory\dashboard\app\growth\page.tsx"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

new_content = content.replace("</div >", "</div>")

if content != new_content:
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Fixed invalid JSX tags.")
else:
    print("No invalid tags found.")
