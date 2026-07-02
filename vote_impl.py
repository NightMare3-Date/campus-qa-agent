import json
f = open("server/static/index.html","r",encoding="utf-8"); t = f.read(); f.close()

# Build the new agent message footer HTML
old_fb_start = "if (role === \"agent\") {"
old_fb_end = "currentMsgEl = div.querySelector(\".bbl\");\n    currentBuffer = \"\";"

# Find the old feedback button block
idx1 = t.find(old_fb_start)
idx2 = t.find(old_fb_end, idx1)
if idx1 > -1 and idx2 > -1:
    idx2 += len(old_fb_end)
    
    new_fb = """if (role === "agent") {
    // 底部操作栏
    var footerDiv = document.createElement("div");
    footerDiv.className = "msg-footer";
    var timeSpan = document.createElement("span");
    timeSpan.className = "msg-time";
    timeSpan.textContent = "刚刚";
    footerDiv.appendChild(timeSpan);
    var actionsDiv = document.createElement("div");
    actionsDiv.className = "msg-actions";
    var likeBtn = document.createElement("button");
    likeBtn.className = "action-btn";
    likeBtn.textContent = "\U0001F44D 有帮助";
    likeBtn.onclick = function() { toggleLike(this); };
    actionsDiv.appendChild(likeBtn);
    var dislikeBtn = document.createElement("button");
    dislikeBtn.className = "action-btn";
    dislikeBtn.textContent = "\U0001F44E 没帮到我";
    dislikeBtn.onclick = function() { toggleDislike(this); };
    actionsDiv.appendChild(dislikeBtn);
    footerDiv.appendChild(actionsDiv);
    div.appendChild(footerDiv);
    var panel = document.createElement("div");
    panel.className = "feedback-panel";
    var p1 = document.createElement("p");
    p1.textContent = "请告诉我们哪里不够好（可选）";
    panel.appendChild(p1);
    var ta = document.createElement("textarea");
    ta.rows = 2;
    ta.placeholder = "信息不准确、没有回答到点上...";
    panel.appendChild(ta);
    var pa = document.createElement("div");
    pa.className = "panel-actions";
    var cancelBtn = document.createElement("button");
    cancelBtn.className = "btn-secondary";
    cancelBtn.textContent = "取消";
    cancelBtn.onclick = function() { this.closest(".feedback-panel").classList.remove("show"); };
    pa.appendChild(cancelBtn);
    var submitBtn = document.createElement("button");
    submitBtn.textContent = "提交反馈";
    submitBtn.onclick = function() { submitFeedback(this); };
    pa.appendChild(submitBtn);
    panel.appendChild(pa);
    div.appendChild(panel);
    currentMsgEl = div.querySelector(".bbl");
    currentBuffer = "";
  }"""
    
    t = t[:idx1] + new_fb + t[idx2:]
    open("server/static/index.html","w",encoding="utf-8").write(t)
    print("OK")
else:
    print("NOT FOUND")
