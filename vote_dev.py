f = open("server/static/index.html","r",encoding="utf-8"); lines = f.readlines(); f.close()

new_lines = []
skip = False
for i, line in enumerate(lines):
    # Start of the old feedback button block
    if 'if (role === "agent") {' in line and 'fbBtn' in ''.join(lines[i:i+30]):
        skip = True
        # Write the new block
        new_lines.append('  if (role === "agent") {\n')
        new_lines.append('    var footerDiv = document.createElement("div");\n')
        new_lines.append('    footerDiv.className = "msg-footer";\n')
        new_lines.append('    var timeSpan = document.createElement("span");\n')
        new_lines.append('    timeSpan.className = "msg-time";\n')
        new_lines.append('    timeSpan.textContent = "刚刚";\n')
        new_lines.append('    footerDiv.appendChild(timeSpan);\n')
        new_lines.append('    var actionsDiv = document.createElement("div");\n')
        new_lines.append('    actionsDiv.className = "msg-actions";\n')
        new_lines.append('    var likeBtn = document.createElement("button");\n')
        new_lines.append('    likeBtn.className = "action-btn";\n')
        new_lines.append('    likeBtn.textContent = "\U0001F44D 有帮助";\n')
        new_lines.append('    likeBtn.onclick = function() { toggleLike(this); };\n')
        new_lines.append('    actionsDiv.appendChild(likeBtn);\n')
        new_lines.append('    var dislikeBtn = document.createElement("button");\n')
        new_lines.append('    dislikeBtn.className = "action-btn";\n')
        new_lines.append('    dislikeBtn.textContent = "\U0001F44E 没帮到我";\n')
        new_lines.append('    dislikeBtn.onclick = function() { toggleDislike(this); };\n')
        new_lines.append('    actionsDiv.appendChild(dislikeBtn);\n')
        new_lines.append('    footerDiv.appendChild(actionsDiv);\n')
        new_lines.append('    div.appendChild(footerDiv);\n')
        # Feedback panel
        new_lines.append('    var panel = document.createElement("div");\n')
        new_lines.append('    panel.className = "feedback-panel";\n')
        new_lines.append('    var p = document.createElement("p");\n')
        new_lines.append('    p.textContent = "请告诉我们哪里不够好（可选）";\n')
        new_lines.append('    panel.appendChild(p);\n')
        new_lines.append('    var ta = document.createElement("textarea");\n')
        new_lines.append('    ta.rows = 2;\n')
        new_lines.append('    ta.placeholder = "信息不准确、没有回答到点上...";\n')
        new_lines.append('    panel.appendChild(ta);\n')
        new_lines.append('    var pa = document.createElement("div");\n')
        new_lines.append('    pa.className = "panel-actions";\n')
        new_lines.append('    var cancelBtn = document.createElement("button");\n')
        new_lines.append('    cancelBtn.className = "btn-secondary";\n')
        new_lines.append('    cancelBtn.textContent = "取消";\n')
        new_lines.append('    cancelBtn.onclick = function() { this.closest(".feedback-panel").classList.remove("show"); };\n')
        new_lines.append('    pa.appendChild(cancelBtn);\n')
        new_lines.append('    var subBtn = document.createElement("button");\n')
        new_lines.append('    subBtn.textContent = "提交反馈";\n')
        new_lines.append('    subBtn.onclick = function() { submitFeedback(this); };\n')
        new_lines.append('    pa.appendChild(subBtn);\n')
        new_lines.append('    panel.appendChild(pa);\n')
        new_lines.append('    div.appendChild(panel);\n')
        new_lines.append('    currentMsgEl = div.querySelector(".bbl");\n')
        new_lines.append('    currentBuffer = "";\n')
        new_lines.append('  }\n')
    elif skip and 'currentMsgEl = div.querySelector(".bbl");' in line:
        skip = False
        continue
    elif skip and 'currentBuffer = "";' in line:
        continue
    elif skip and line.strip() == "}":
        skip = False
        continue
    elif skip:
        continue
    else:
        new_lines.append(line)

open("server/static/index.html","w",encoding="utf-8").write("".join(new_lines))
print("OK")
