(function () {
  "use strict";

  const fileInput = document.getElementById("fileInput");
  const dropZone = document.getElementById("dropZone");
  const statusEl = document.getElementById("status");
  const placeholder = document.getElementById("placeholder");
  const imageShell = document.getElementById("imageShell");
  const previewImg = document.getElementById("previewImg");
  const swatch = document.getElementById("swatch");
  const pixelName = document.getElementById("pixelName");
  const pixelRgb = document.getElementById("pixelRgb");
  const pixelHex = document.getElementById("pixelHex");
  const dominantBars = document.getElementById("dominantBars");
  const paletteList = document.getElementById("paletteList");

  let uploadId = null;
  let imageWidth = 0;
  let imageHeight = 0;

  function setStatus(msg, type) {
    statusEl.textContent = msg || "";
    statusEl.className = "status" + (type ? " " + type : "");
  }

  function resetViewer() {
    uploadId = null;
    imageWidth = 0;
    imageHeight = 0;
    placeholder.hidden = false;
    imageShell.hidden = true;
    previewImg.removeAttribute("src");
    dominantBars.innerHTML = "";
    paletteList.innerHTML = "";
    swatch.style.background = "";
    pixelName.textContent = "—";
    pixelRgb.innerHTML = "<code>—</code>";
    pixelHex.innerHTML = "<code>—</code>";
  }

  function renderDominant(colors) {
    dominantBars.innerHTML = "";
    paletteList.innerHTML = "";
    if (!colors || !colors.length) return;

    const totalWeight = colors.length;
    colors.forEach(function (c) {
      const seg = document.createElement("div");
      seg.className = "bar-seg";
      seg.style.background = c.hex;
      seg.style.flex = String(1);
      seg.title = c.name + " " + c.hex;
      dominantBars.appendChild(seg);
    });

    colors.forEach(function (c) {
      const li = document.createElement("li");
      li.innerHTML =
        '<span class="palette-dot" style="background:' +
        c.hex +
        '"></span>' +
        '<span class="name" title="' +
        escapeAttr(c.name) +
        '">' +
        escapeHtml(c.name) +
        "</span>" +
        '<span class="rgb">' +
        c.r +
        ", " +
        c.g +
        ", " +
        c.b +
        "</span>";
      paletteList.appendChild(li);
    });
  }

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  function escapeAttr(s) {
    return String(s).replace(/&/g, "&amp;").replace(/"/g, "&quot;");
  }

  async function uploadFile(file) {
    if (!file || !file.type.startsWith("image/")) {
      setStatus("Please choose an image file.", "error");
      return;
    }

    setStatus("Uploading and analyzing palette…", "loading");
    resetViewer();
    previewImg.alt = "Uploading…";

    const fd = new FormData();
    fd.append("image", file);

    try {
      const res = await fetch("/api/upload", {
        method: "POST",
        body: fd,
      });
      const data = await res.json().catch(function () {
        return {};
      });

      if (!res.ok || !data.ok) {
        setStatus(data.error || "Upload failed (" + res.status + ").", "error");
        return;
      }

      uploadId = data.upload_id;
      imageWidth = data.width;
      imageHeight = data.height;

      previewImg.onload = function () {
        previewImg.onload = null;
      };
      previewImg.src = data.image_url + "?t=" + Date.now();

      placeholder.hidden = true;
      imageShell.hidden = false;

      renderDominant(data.dominant_colors);
      setStatus("Ready — click the image to sample a color.", "success");
    } catch (e) {
      console.error(e);
      setStatus("Network error. Is the server running?", "error");
    }
  }

  function imageCoordsFromEvent(e) {
    const rect = previewImg.getBoundingClientRect();
    const nw = previewImg.naturalWidth;
    const nh = previewImg.naturalHeight;
    const ow = previewImg.offsetWidth;
    const oh = previewImg.offsetHeight;
    if (!nw || !nh || !ow || !oh) return null;

    const x = Math.floor(((e.clientX - rect.left) / ow) * nw);
    const y = Math.floor(((e.clientY - rect.top) / oh) * nh);
    return { x: x, y: y };
  }

  async function onImageClick(e) {
    if (!uploadId) return;

    const coords = imageCoordsFromEvent(e);
    if (coords === null) {
      setStatus("Image not loaded yet.", "error");
      return;
    }

    const x = Math.max(0, Math.min(coords.x, imageWidth - 1));
    const y = Math.max(0, Math.min(coords.y, imageHeight - 1));

    setStatus("Sampling pixel…", "loading");

    try {
      const res = await fetch("/api/pixel", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ upload_id: uploadId, x: x, y: y }),
      });
      const data = await res.json().catch(function () {
        return {};
      });

      if (!res.ok || !data.ok) {
        setStatus(data.error || "Could not read pixel.", "error");
        return;
      }

      swatch.style.background = data.hex;
      pixelName.textContent = data.name;
      pixelRgb.innerHTML =
        "<code>" + data.r + ", " + data.g + ", " + data.b + "</code>";
      pixelHex.innerHTML = "<code>" + data.hex + "</code>";
      setStatus("Pixel at (" + x + ", " + y + ")", "success");
    } catch (err) {
      console.error(err);
      setStatus("Request failed.", "error");
    }
  }

  dropZone.addEventListener("click", function () {
    fileInput.click();
  });

  fileInput.addEventListener("change", function () {
    const f = fileInput.files && fileInput.files[0];
    if (f) uploadFile(f);
    fileInput.value = "";
  });

  ["dragenter", "dragover", "dragleave", "drop"].forEach(function (ev) {
    dropZone.addEventListener(ev, function (e) {
      e.preventDefault();
      e.stopPropagation();
    });
  });

  dropZone.addEventListener("dragover", function () {
    dropZone.classList.add("dragover");
  });

  dropZone.addEventListener("dragleave", function () {
    dropZone.classList.remove("dragover");
  });

  dropZone.addEventListener("drop", function (e) {
    dropZone.classList.remove("dragover");
    const f = e.dataTransfer.files && e.dataTransfer.files[0];
    if (f) uploadFile(f);
  });

  previewImg.addEventListener("click", onImageClick);
})();
