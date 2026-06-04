with open('app.py', 'r') as f:
    content = f.read()
content = content.replace('\\"', '"')
with open('app.py', 'w') as f:
    f.write(content)
print("Done fixing app.py")
