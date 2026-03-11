(() => {
    const dropZone = document.getElementById("drop-zone");
    if (!dropZone) {
        return;
    }

    const fileInput = dropZone.querySelector('input[type="file"]');
    const fileList = document.getElementById("file-list");

    const updateList = () => {
        const files = Array.from(fileInput.files || []);
        if (!files.length) {
            fileList.textContent = "Aucun fichier selectionne.";
            return;
        }
        fileList.textContent = files.map((file) => file.name).join(", ");
    };

    ["dragenter", "dragover"].forEach((eventName) => {
        dropZone.addEventListener(eventName, (event) => {
            event.preventDefault();
            dropZone.classList.add("active");
        });
    });

    ["dragleave", "drop"].forEach((eventName) => {
        dropZone.addEventListener(eventName, (event) => {
            event.preventDefault();
            dropZone.classList.remove("active");
        });
    });

    dropZone.addEventListener("drop", (event) => {
        fileInput.files = event.dataTransfer.files;
        updateList();
    });

    fileInput.addEventListener("change", updateList);
})();
