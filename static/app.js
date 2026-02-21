(() => {
    "use strict";

    // DOM elements
    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("file-input");
    const progressCard = document.getElementById("progress-card");
    const progressBar = document.getElementById("progress-bar");
    const progressLabel = document.getElementById("progress-label");
    const progressPercent = document.getElementById("progress-percent");
    const resultsCard = document.getElementById("results-card");
    const fileList = document.getElementById("file-list");
    const downloadAllBtn = document.getElementById("download-all-btn");
    const existingCard = document.getElementById("existing-card");
    const existingList = document.getElementById("existing-list");

    let convertedFiles = [];

    // ==================== Drag & Drop ====================

    dropzone.addEventListener("click", () => fileInput.click());

    dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.classList.add("drag-over");
    });

    dropzone.addEventListener("dragleave", (e) => {
        e.preventDefault();
        dropzone.classList.remove("drag-over");
    });

    dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("drag-over");
        const files = [...e.dataTransfer.files].filter(f =>
            f.name.toLowerCase().endsWith(".dwfx")
        );
        if (files.length) uploadFiles(files);
    });

    fileInput.addEventListener("change", () => {
        const files = [...fileInput.files];
        if (files.length) uploadFiles(files);
        fileInput.value = "";
    });

    // ==================== Upload ====================

    async function uploadFiles(files) {
        progressCard.classList.remove("hidden");
        progressBar.style.width = "0%";
        progressLabel.textContent = `Uploading ${files.length} file${files.length > 1 ? "s" : ""}...`;
        progressPercent.textContent = "0%";

        const formData = new FormData();
        files.forEach(f => formData.append("files", f));

        try {
            const xhr = new XMLHttpRequest();

            const response = await new Promise((resolve, reject) => {
                xhr.upload.addEventListener("progress", (e) => {
                    if (e.lengthComputable) {
                        const pct = Math.round((e.loaded / e.total) * 50);
                        progressBar.style.width = pct + "%";
                        progressPercent.textContent = pct + "%";
                    }
                });

                xhr.addEventListener("load", () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        resolve(JSON.parse(xhr.responseText));
                    } else {
                        reject(new Error(`HTTP ${xhr.status}`));
                    }
                });

                xhr.addEventListener("error", () => reject(new Error("Network error")));

                xhr.open("POST", "/upload");
                xhr.send(formData);
            });

            // Simulate conversion progress (server already finished)
            progressLabel.textContent = "Converting...";
            await animateProgress(50, 100);

            progressLabel.textContent = "Done!";
            progressPercent.textContent = "100%";

            // Display results
            displayResults(response.results);

            // Hide progress after a brief delay
            setTimeout(() => {
                progressCard.classList.add("hidden");
            }, 1500);

        } catch (err) {
            progressLabel.textContent = "Error: " + err.message;
            progressBar.style.width = "100%";
            progressBar.style.background = "var(--error)";
            setTimeout(() => {
                progressCard.classList.add("hidden");
                progressBar.style.background = "";
            }, 3000);
        }
    }

    function animateProgress(from, to) {
        return new Promise(resolve => {
            let current = from;
            const step = () => {
                current += 2;
                if (current >= to) {
                    progressBar.style.width = to + "%";
                    progressPercent.textContent = to + "%";
                    resolve();
                    return;
                }
                progressBar.style.width = current + "%";
                progressPercent.textContent = current + "%";
                requestAnimationFrame(step);
            };
            requestAnimationFrame(step);
        });
    }

    // ==================== Results ====================

    function displayResults(results) {
        resultsCard.classList.remove("hidden");

        results.forEach(r => {
            if (r.success && r.pdf_name) {
                convertedFiles.push(r.pdf_name);
            }
            const li = createFileItem(r);
            fileList.appendChild(li);
        });

        downloadAllBtn.classList.toggle("hidden", convertedFiles.length === 0);
    }

    function createFileItem(result) {
        const li = document.createElement("li");
        li.className = "file-item";

        if (result.success) {
            li.innerHTML = `
                <div class="file-info">
                    <div class="file-icon pdf">PDF</div>
                    <div>
                        <div class="file-name">${escapeHtml(result.pdf_name)}</div>
                        <div class="file-status success">✓ Converted</div>
                    </div>
                </div>
                <a class="btn btn-download" href="/download/${encodeURIComponent(result.pdf_name)}" download>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                        <polyline points="7 10 12 15 17 10"/>
                        <line x1="12" y1="15" x2="12" y2="3"/>
                    </svg>
                    Download
                </a>
            `;
        } else {
            li.innerHTML = `
                <div class="file-info">
                    <div class="file-icon error">ERR</div>
                    <div>
                        <div class="file-name">${escapeHtml(result.name)}</div>
                        <div class="file-status error">${escapeHtml(result.error || "Unknown error")}</div>
                    </div>
                </div>
            `;
        }

        return li;
    }

    // ==================== Download All ====================

    downloadAllBtn.addEventListener("click", async () => {
        if (!convertedFiles.length) return;

        downloadAllBtn.disabled = true;
        downloadAllBtn.textContent = "Preparing ZIP...";

        try {
            const res = await fetch("/download-all", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ files: convertedFiles }),
            });

            if (!res.ok) throw new Error("Failed to create ZIP");

            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "converted.zip";
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
        } catch (err) {
            alert("Error downloading ZIP: " + err.message);
        } finally {
            downloadAllBtn.disabled = false;
            downloadAllBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                    <polyline points="7 10 12 15 17 10"/>
                    <line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
                Download All (.zip)
            `;
        }
    });

    // ==================== Load Existing Files ====================

    async function loadExistingFiles() {
        try {
            const res = await fetch("/api/files");
            const data = await res.json();
            if (data.files && data.files.length > 0) {
                existingCard.classList.remove("hidden");
                data.files.forEach(name => {
                    const li = createFileItem({ success: true, pdf_name: name, name });
                    existingList.appendChild(li);
                });
            }
        } catch (e) {
            // silently ignore
        }
    }

    loadExistingFiles();

    // ==================== Helpers ====================

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }
})();
