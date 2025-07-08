window.addEventListener("load", init, false);

function addField() {
    const input = document.createElement("input");
    input.type = "text";
    input.className = "fieldInput";
    input.placeholder = "欄位名稱";
    document.getElementById("fieldContainer").appendChild(document.createElement("br"));
    document.getElementById("fieldContainer").appendChild(input);
}

function getFieldTitles() {
    const inputs = document.querySelectorAll("#fieldContainer .fieldInput");
    const titles = [];
    inputs.forEach(input => {
        const val = input.value.trim();
        if (val) titles.push(val);
    });

    return titles;
}

function init() {
    document.getElementById("generateForm").addEventListener("submit", async function (e) {
        e.preventDefault();
        const data = {
            course_name: document.getElementById("courseName").value,
            unit_name: document.getElementById("unitName").value,
            student_id: "",  // default value
            student_name: "",  // default value
            fields: getFieldTitles()
        };
        console.log(data);
        const response = await fetch("/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });
        if (response.ok) {
            const json = await response.json();
            if (json.download_url) {
                const link = document.createElement("a");
                console.log(link);
                link.href = json.download_url;
                link.download = "Exercise.odt";
                document.body.appendChild(link);
                link.click();
                link.remove();
            } else {
                alert("產生失敗：無下載連結");
            }
        } else {
            alert("產生失敗！");
        }
    });

    document.getElementById("extractForm").addEventListener("submit", async function (e) {
        e.preventDefault();
        const formData = new FormData(this);
        const fields = getFieldTitles();  // 自己定義的函數，取得欄位陣列
        formData.append("fields_json", JSON.stringify(fields));  // ←傳 JSON 字串

        const response = await fetch("/extract", {
            method: "POST",
            body: formData
        });
        const resultDiv = document.getElementById("result");
        resultDiv.innerHTML = "";
        if (response.ok) {
            const data = await response.json();
            if (data.answers) {
                resultDiv.innerHTML += "<h3>擷取結果：</h3>";
                const table = document.createElement("table");
                for (const [key, value] of Object.entries(data.answers)) {
                    const row = table.insertRow();
                    row.insertCell().textContent = key;
                    row.insertCell().textContent = value;
                }
                resultDiv.appendChild(table);
            }
            if (data.images) {
                resultDiv.innerHTML += "<h3>擷取圖片：</h3>";
                for (const [filename, base64] of Object.entries(data.images)) {
                    const img = document.createElement("img");
                    img.src = `data:image/png;base64,${base64}`;
                    img.style.maxWidth = "300px";
                    img.style.margin = "10px";
                    resultDiv.appendChild(img);
                }
            }
        } else {
            alert("擷取失敗！");
        }
    });

    document.getElementById("extractFolderForm").addEventListener("submit", async function (e) {
        e.preventDefault();
        const form = document.getElementById("extractFolderForm");
        const formData = new FormData();
        for (const file of form.querySelector("input[type='file']").files) {
            formData.append("files", file);
        }

        const fields = getFieldTitles();
        formData.append("fields_json", JSON.stringify(fields));

        const response = await fetch("/extract-folder", {
            method: "POST",
            body: formData
        });

        const resultDiv = document.getElementById("result");
        resultDiv.innerHTML = "";

        if (response.ok) {
            const data = await response.json();
            let markdownWithImages = "";
            let markdownWithoutImages = "";

            for (const [fileName, fileData] of Object.entries(data)) {
                // 將 base64 圖片包為可點擊的 URL
                Object.keys(fileData.images).forEach((filename) => {
                    const base64 = fileData.images[filename];
                    fileData.images[filename] = `data:image/png;base64,${base64}`;
                });

                // 顯示結果在畫面上
                resultDiv.innerHTML += `<h3>${fileName}</h3>`;
                const table = document.createElement("table");
                table.style.border = "1";
                table.style.cellPadding = "5";
                table.style.marginBottom = "10px";

                // Markdown 表頭
                markdownWithImages += `## ${fileName}\n\n| 欄位 | 作答 |\n|------|------|\n`;
                markdownWithoutImages += `## ${fileName}\n\n| 欄位 | 作答 |\n|------|------|\n`;

                for (const [key, value] of Object.entries(fileData.answers || {})) {
                    const row = table.insertRow();
                    row.insertCell().textContent = key;
                    row.insertCell().textContent = value || "";
                    markdownWithImages += `| ${key} | ${value || ""} |\n`;
                    markdownWithoutImages += `| ${key} | ${value || ""} |\n`;
                }

                resultDiv.appendChild(table);

                // 附加圖片
                if (fileData.images && Object.keys(fileData.images).length > 0) {
                    resultDiv.innerHTML += "<div>圖片檔案：</div>";
                    const ul = document.createElement("ul");
                    for (const [filename, base64] of Object.entries(fileData.images)) {
                        const li = document.createElement("li");
                        const a = document.createElement("a");
                        a.href = base64;
                        a.download = filename;
                        a.textContent = filename;
                        li.appendChild(a);
                        ul.appendChild(li);

                        markdownWithImages += `\n![${filename}](${base64})\n`;
                        // 不加入圖片至 markdownWithoutImages
                    }
                    resultDiv.appendChild(ul);
                }

                markdownWithImages += `\n---\n\n`;
                markdownWithoutImages += `\n---\n\n`;
            }

            // 建立兩個 Blob 並提供下載連結
            const withImgBlob = new Blob([markdownWithImages], { type: "text/markdown" });
            const withImgUrl = URL.createObjectURL(withImgBlob);
            const withImgLink = document.createElement("a");
            withImgLink.href = withImgUrl;
            withImgLink.download = "作答彙整_含圖片.md";
            withImgLink.textContent = "📥 下載 Markdown (含圖片)";
            withImgLink.style.display = "block";
            withImgLink.style.marginTop = "20px";
            resultDiv.appendChild(withImgLink);

            const noImgBlob = new Blob([markdownWithoutImages], { type: "text/markdown" });
            const noImgUrl = URL.createObjectURL(noImgBlob);
            const noImgLink = document.createElement("a");
            noImgLink.href = noImgUrl;
            noImgLink.download = "作答彙整_無圖片.md";
            noImgLink.textContent = "📥 下載 Markdown (無圖片)";
            noImgLink.style.display = "block";
            resultDiv.appendChild(noImgLink);
        } else {
            alert("資料夾擷取失敗");
        }
    });
}