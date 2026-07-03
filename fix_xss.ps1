$file = "C:\Users\’≈∫Õ¿§\Documents\AIAgent\server\static\index.html"
$content = Get-Content $file -Raw

# 1. Add DOMPurify after marked.js
$content = $content -replace '(<script src="https://cdn\.jsdelivr\.net/npm/marked/marked\.min\.js"></script>\s*)', "$1<script src="https://cdn.jsdelivr.net/npm/dompurify@3.1.6/dist/purify.min.js"></script>
"

# 2. Modify addMsg
$old1 = "var rendered = role === 'agent' && typeof marked !== 'undefined' ? marked.parse(content) : content;"
$new1 = "var rawHtml = marked.parse(content);
  var rendered = role === 'agent' && typeof marked !== 'undefined' ? (typeof DOMPurify !== 'undefined' ? DOMPurify.sanitize(rawHtml) : rawHtml) : content;"
$content = $content -replace [regex]::Escape($old1), $new1

# 3. Modify appendToken
$old2 = "if (typeof marked !== 'undefined' && currentMsgEl.parentElement && currentMsgEl.parentElement.classList.contains('agent')) { currentMsgEl.innerHTML = marked.parse(currentBuffer); } else { currentMsgEl.textContent = currentBuffer; }"
$new2 = "if (typeof marked !== 'undefined' && currentMsgEl.parentElement && currentMsgEl.parentElement.classList.contains('agent')) { var rawHtml = marked.parse(currentBuffer); currentMsgEl.innerHTML = typeof DOMPurify !== 'undefined' ? DOMPurify.sanitize(rawHtml) : rawHtml; } else { currentMsgEl.textContent = currentBuffer; }"
$content = $content -replace [regex]::Escape($old2), $new2

Set-Content $file -Value $content -NoNewline
Write-Host "Done"
