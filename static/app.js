const audio = document.getElementById("audio");
const bar = document.getElementById("bar");

function loadSongs() {
  fetch("/songs")
    .then(res => res.json())
    .then(data => {
      const list = document.getElementById("songs");
      list.innerHTML = "";
      data.forEach(song => {
        const li = document.createElement("li");
        li.innerText = song;
        li.onclick = () => {
          audio.src = "/songs/" + song;
          audio.play();
        };
        list.appendChild(li);
      });
    });
}

function download() {
  const url = document.getElementById("url").value;
  fetch("/download", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url })
  });
}

setInterval(() => {
  fetch("/progress")
    .then(res => res.json())
    .then(d => {
      bar.style.width = d.progress + "%";
      if (d.progress === 100) loadSongs();
    });
}, 500);

loadSongs();
